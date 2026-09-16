from pathlib import Path
import pytest
from werkzeug.security import generate_password_hash

from server.app import create_app
from server.config import build_config, get_default_config_path, validate_security_config
from server.database import get_db


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "DATA_ROOT": tmp_path / "batcave",
            "DATABASE_PATH": tmp_path / "batcave" / "batcave.db",
            "SECRET_KEY": "test-secret-key-12345",
            "PASSWORD_HASH": generate_password_hash("correct horse battery staple"),
        }
    )
    yield application
    with application.app_context():
        from server.database import close_db

        close_db()


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client


def csrf(client):
    client.get("/login")
    with client.session_transaction() as session:
        return session["csrf_token"]


def login(client):
    return client.post(
        "/login",
        data={"password": "correct horse battery staple", "csrf_token": csrf(client)},
        follow_redirects=False,
    )


def authenticated_csrf(client):
    login(client)
    with client.session_transaction() as session:
        return session["csrf_token"]


def test_dashboard_requires_authentication(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_authenticated_dashboard_loads_successfully(client):
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Dashboard" in html
    assert "COMMAND CENTER" in html
    assert "Quick Actions" in html


def test_dashboard_displays_real_counts(client, app):
    token = authenticated_csrf(client)
    # Create 3 notes
    client.post("/notes/create", data={"title": "Note 1", "content": "A", "csrf_token": token})
    client.post("/notes/create", data={"title": "Note 2", "content": "B", "csrf_token": token})
    client.post("/notes/create", data={"title": "Note 3", "content": "C", "csrf_token": token})

    # Create 2 ideas
    client.post("/ideas/create", data={"content": "Idea 1", "csrf_token": token})
    client.post("/ideas/create", data={"content": "Idea 2", "csrf_token": token})

    # Create 3 projects: 2 Active, 1 Archived
    client.post("/projects/create", data={"name": "Proj 1", "description": "D1", "csrf_token": token})
    client.post("/projects/create", data={"name": "Proj 2", "description": "D2", "csrf_token": token})
    client.post("/projects/create", data={"name": "Proj 3", "description": "D3", "csrf_token": token})

    with app.app_context():
        db = get_db()
        db.execute("UPDATE projects SET status = 'Archived' WHERE name = 'Proj 3'")
        db.commit()

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "3 notes" in html
    assert "2 ideas" in html
    assert "3 projects (2 active)" in html


def test_recent_notes_ordered_correctly(client, app):
    token = authenticated_csrf(client)
    client.post("/notes/create", data={"title": "First Note", "content": "1", "csrf_token": token})
    client.post("/notes/create", data={"title": "Second Note", "content": "2", "csrf_token": token})
    client.post("/notes/create", data={"title": "Third Note", "content": "3", "csrf_token": token})

    with app.app_context():
        db = get_db()
        # Explicitly update First Note's updated_at to be the newest
        db.execute(
            "UPDATE notes SET updated_at = '2099-01-01 12:00:00.000' WHERE title = 'First Note'"
        )
        db.commit()
        first_note = db.execute("SELECT id FROM notes WHERE title = 'First Note'").fetchone()

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    pos_first = html.find("First Note")
    pos_third = html.find("Third Note")
    pos_second = html.find("Second Note")
    assert pos_first != -1 and pos_third != -1 and pos_second != -1
    # First Note was updated most recently, so it must appear before Third Note and Second Note
    assert pos_first < pos_third < pos_second
    assert f"/notes/{first_note['id']}" in html


def test_recent_ideas_ordered_correctly(client, app):
    token = authenticated_csrf(client)
    client.post("/ideas/create", data={"content": "Alpha Idea", "csrf_token": token})
    client.post("/ideas/create", data={"content": "Beta Idea", "csrf_token": token})
    client.post("/ideas/create", data={"content": "Gamma Idea", "csrf_token": token})

    with app.app_context():
        gamma = get_db().execute("SELECT id FROM ideas WHERE content = 'Gamma Idea'").fetchone()

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    pos_gamma = html.find("Gamma Idea")
    pos_beta = html.find("Beta Idea")
    pos_alpha = html.find("Alpha Idea")
    assert pos_gamma != -1 and pos_beta != -1 and pos_alpha != -1
    # Newest idea must appear first (created_at DESC, id DESC)
    assert pos_gamma < pos_beta < pos_alpha
    assert f"/ideas/{gamma['id']}" in html


def test_active_projects_shown_and_non_active_filtered(client, app):
    token = authenticated_csrf(client)
    client.post("/projects/create", data={"name": "Active Apollo", "description": "Lunar mission", "csrf_token": token})
    client.post("/projects/create", data={"name": "Paused Gemini", "description": "Earth orbit", "csrf_token": token})
    client.post("/projects/create", data={"name": "Archived Mercury", "description": "Suborbital", "csrf_token": token})

    with app.app_context():
        db = get_db()
        db.execute("UPDATE projects SET status = 'Paused' WHERE name = 'Paused Gemini'")
        db.execute("UPDATE projects SET status = 'Archived' WHERE name = 'Archived Mercury'")
        db.commit()
        apollo = db.execute("SELECT id FROM projects WHERE name = 'Active Apollo'").fetchone()

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Active Apollo is in the active list and links to project detail
    assert "Active Apollo" in html
    assert f"/projects/{apollo['id']}" in html

    # Paused Gemini and Archived Mercury should NOT be in the Active Projects section
    active_section = html[html.find("Active Projects") :]
    assert "Active Apollo" in active_section
    assert "Paused Gemini" not in active_section
    assert "Archived Mercury" not in active_section


def test_quick_action_links_point_to_workflows(client):
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'href="/notes"' in html
    assert 'href="/ideas"' in html
    assert 'href="/projects"' in html
    assert 'href="/files"' in html


def test_storage_summary_on_dashboard(client):
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Storage capacity" in html
    assert "Used" in html
    assert "Free" in html
    assert "Total" in html


def test_dashboard_does_not_leak_secrets_or_absolute_paths(client, app):
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # Ensure secrets and database path do not leak
    assert "test-secret-key-12345" not in html
    assert "correct horse battery staple" not in html
    assert str(app.config["DATA_ROOT"]) not in html
    assert str(app.config["DATABASE_PATH"]) not in html


def test_navigation_includes_dashboard_and_workspaces(client):
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<a href="/">Dashboard</a>' in html
    assert '<a href="/files">Files</a>' in html
    assert '<a href="/notes">Notes</a>' in html
    assert '<a href="/ideas">Ideas</a>' in html
    assert '<a href="/projects">Projects</a>' in html


def test_configuration_default_discovery(monkeypatch, tmp_path):
    monkeypatch.delenv("BATCAVE_CONFIG_FILE", raising=False)
    monkeypatch.delenv("BATCAVE_SECRET_KEY", raising=False)
    monkeypatch.delenv("BATCAVE_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    default_file = tmp_path / ".config" / "batcave-cloud" / "batcave.env"
    default_file.parent.mkdir(parents=True, exist_ok=True)
    default_file.write_text(
        "BATCAVE_SECRET_KEY=discovered-secret-999\n"
        "BATCAVE_PASSWORD_HASH=discovered-hash-888\n",
        encoding="utf-8",
    )

    config = build_config()
    assert config["SECRET_KEY"] == "discovered-secret-999"
    assert config["PASSWORD_HASH"] == "discovered-hash-888"


def test_configuration_explicit_file_precedence(monkeypatch, tmp_path):
    monkeypatch.delenv("BATCAVE_SECRET_KEY", raising=False)
    monkeypatch.delenv("BATCAVE_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # Default file
    default_file = tmp_path / ".config" / "batcave-cloud" / "batcave.env"
    default_file.parent.mkdir(parents=True, exist_ok=True)
    default_file.write_text(
        "BATCAVE_SECRET_KEY=default-secret\n"
        "BATCAVE_PASSWORD_HASH=default-hash\n",
        encoding="utf-8",
    )

    # Explicit custom file
    custom_file = tmp_path / "custom" / "my_custom.env"
    custom_file.parent.mkdir(parents=True, exist_ok=True)
    custom_file.write_text(
        "BATCAVE_SECRET_KEY=explicit-secret\n"
        "BATCAVE_PASSWORD_HASH=explicit-hash\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("BATCAVE_CONFIG_FILE", str(custom_file))

    config = build_config()
    # Explicit file must win
    assert config["SECRET_KEY"] == "explicit-secret"
    assert config["PASSWORD_HASH"] == "explicit-hash"


def test_configuration_explicit_missing_file_raises_error(monkeypatch, tmp_path):
    nonexistent = tmp_path / "missing.env"
    monkeypatch.setenv("BATCAVE_CONFIG_FILE", str(nonexistent))

    with pytest.raises(RuntimeError) as exc_info:
        build_config()
    assert "BATCAVE_CONFIG_FILE does not exist" in str(exc_info.value)


def test_missing_configuration_produces_clear_failure_and_no_secret_generation(monkeypatch, tmp_path):
    monkeypatch.delenv("BATCAVE_CONFIG_FILE", raising=False)
    monkeypatch.delenv("BATCAVE_SECRET_KEY", raising=False)
    monkeypatch.delenv("BATCAVE_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    config = build_config()
    assert config["SECRET_KEY"] is None
    assert config["PASSWORD_HASH"] is None

    with pytest.raises(RuntimeError) as exc_info:
        validate_security_config(config)

    message = str(exc_info.value)
    assert "Missing required configuration" in message
    assert "create-config" in message

    # Verify no file was created on disk
    default_path = get_default_config_path()
    assert not default_path.exists()
