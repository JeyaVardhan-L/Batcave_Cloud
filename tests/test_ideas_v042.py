import pytest
from werkzeug.security import generate_password_hash

from server.app import create_app


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "DATA_ROOT": tmp_path / "batcave",
            "DATABASE_PATH": tmp_path / "batcave" / "batcave.db",
            "SECRET_KEY": "test-secret-key",
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
    )


def logged_in_token(client):
    login(client)
    with client.session_transaction() as session:
        return session["csrf_token"]


def create_idea(client, content="Original idea"):
    response = client.post(
        "/ideas/create",
        data={"content": content, "csrf_token": logged_in_token(client)},
    )
    assert response.status_code == 302
    return response


def idea_row(app, idea_id):
    with app.app_context():
        from server.database import get_db

        return get_db().execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()


def get_latest_idea(app):
    with app.app_context():
        from server.database import get_db

        return get_db().execute("SELECT * FROM ideas ORDER BY id DESC LIMIT 1").fetchone()


def test_create_idea(client, app):
    create_idea(client, "Invent a hoverboard")
    idea = get_latest_idea(app)
    assert idea is not None
    assert idea["content"] == "Invent a hoverboard"


def test_create_empty_idea_rejected(client, app):
    token = logged_in_token(client)
    response = client.post("/ideas/create", data={"content": "   ", "csrf_token": token})
    assert response.status_code == 302
    with app.app_context():
        from server.database import get_db

        assert get_db().execute("SELECT COUNT(*) FROM ideas").fetchone()[0] == 0


def test_edit_idea_view(client, app):
    create_idea(client, "Inspect this idea")
    idea = get_latest_idea(app)
    response = client.get(f"/ideas/{idea['id']}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Edit Idea" in html
    assert "Inspect this idea" in html
    assert idea["created_at"] in html


def test_update_idea(client, app):
    create_idea(client, "Initial thought")
    original = get_latest_idea(app)
    token = logged_in_token(client)

    response = client.post(
        f"/ideas/{original['id']}/update",
        data={"content": "Polished breakthrough", "csrf_token": token},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/ideas/{original['id']}")

    updated = idea_row(app, original["id"])
    assert updated["content"] == "Polished breakthrough"
    assert updated["id"] == original["id"]
    assert updated["created_at"] == original["created_at"]


def test_update_idea_empty_content_rejected(client, app):
    create_idea(client, "Solid idea")
    original = get_latest_idea(app)
    token = logged_in_token(client)

    response = client.post(
        f"/ideas/{original['id']}/update",
        data={"content": "   ", "csrf_token": token},
    )
    assert response.status_code == 302
    updated = idea_row(app, original["id"])
    assert updated["content"] == "Solid idea"


def test_delete_idea(client, app):
    create_idea(client, "Discard me")
    idea = get_latest_idea(app)
    response = client.post(
        f"/ideas/delete/{idea['id']}",
        data={"csrf_token": logged_in_token(client)},
    )
    assert response.status_code == 302
    assert idea_row(app, idea["id"]) is None


def test_search_by_content(client):
    create_idea(client, "Solar powered car")
    create_idea(client, "Lunar rover module")
    create_idea(client, "SOLAR battery storage")

    solar_results = client.get("/ideas?q=solar").get_data(as_text=True)
    assert "Solar powered car" in solar_results
    assert "SOLAR battery storage" in solar_results
    assert "Lunar rover module" not in solar_results

    lunar_results = client.get("/ideas?q=LUNAR").get_data(as_text=True)
    assert "Lunar rover module" in lunar_results
    assert "Solar powered car" not in lunar_results

    empty_match = client.get("/ideas?q=fusion").get_data(as_text=True)
    assert "No matching ideas were found." in empty_match


def test_empty_search(client):
    create_idea(client, "First chronological")
    create_idea(client, "Second chronological")

    page_blank = client.get("/ideas?q=").get_data(as_text=True)
    assert "First chronological" in page_blank
    assert "Second chronological" in page_blank

    page_spaces = client.get("/ideas?q=   ").get_data(as_text=True)
    assert "First chronological" in page_spaces
    assert "Second chronological" in page_spaces

    # Verify newest first order
    first_idx = page_blank.index("First chronological")
    second_idx = page_blank.index("Second chronological")
    assert second_idx < first_idx


def test_nonexistent_idea(client):
    token = logged_in_token(client)
    assert client.get("/ideas/99999").status_code == 404
    assert client.post("/ideas/99999/update", data={"content": "Ghost", "csrf_token": token}).status_code == 404
    assert client.post("/ideas/delete/99999", data={"csrf_token": token}).status_code == 404


def test_idea_update_requires_authentication(client, app):
    create_idea(client, "Secret plan")
    idea = get_latest_idea(app)

    with client.session_transaction() as session:
        session.clear()

    get_resp = client.get(f"/ideas/{idea['id']}")
    assert get_resp.status_code == 302
    assert "/login" in get_resp.headers["Location"]

    post_resp = client.post(
        f"/ideas/{idea['id']}/update",
        data={"content": "Hacked plan", "csrf_token": "any"},
    )
    assert post_resp.status_code == 302
    assert "/login" in post_resp.headers["Location"]

    assert idea_row(app, idea["id"])["content"] == "Secret plan"


def test_idea_update_requires_csrf(client, app):
    create_idea(client, "Protected thought")
    idea = get_latest_idea(app)
    login(client)

    # Missing CSRF
    no_csrf = client.post(f"/ideas/{idea['id']}/update", data={"content": "No token"})
    assert no_csrf.status_code == 400

    # Invalid CSRF
    invalid_csrf = client.post(
        f"/ideas/{idea['id']}/update",
        data={"content": "Bad token", "csrf_token": "invalid_value"},
    )
    assert invalid_csrf.status_code == 400

    assert idea_row(app, idea["id"])["content"] == "Protected thought"
