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


def create_project(client, name="Project Apollo", description="Moon mission"):
    response = client.post(
        "/projects/create",
        data={"name": name, "description": description, "csrf_token": logged_in_token(client)},
    )
    assert response.status_code == 302
    return response


def project_row(app, project_id):
    with app.app_context():
        from server.database import get_db

        return get_db().execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def get_latest_project(app):
    with app.app_context():
        from server.database import get_db

        return get_db().execute("SELECT * FROM projects ORDER BY id DESC LIMIT 1").fetchone()


def test_create_project(client, app):
    create_project(client, "Mission Mars", "Rover exploration")
    project = get_latest_project(app)
    assert project is not None
    assert project["name"] == "Mission Mars"
    assert project["description"] == "Rover exploration"
    assert project["status"] == "Active"
    assert project["folder_name"] == f"project-{project['id']}"

    folder_path = app.config["DATA_ROOT"] / "projects" / project["folder_name"]
    assert folder_path.is_dir()


def test_create_project_empty_name_rejected(client, app):
    token = logged_in_token(client)
    response = client.post("/projects/create", data={"name": "   ", "description": "No name", "csrf_token": token})
    assert response.status_code == 302
    with app.app_context():
        from server.database import get_db

        assert get_db().execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0


def test_project_detail_page(client, app):
    create_project(client, "Deep Sea Probe", "Ocean exploration")
    project = get_latest_project(app)
    response = client.get(f"/projects/{project['id']}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Deep Sea Probe" in html
    assert "Ocean exploration" in html
    assert "Active" in html
    assert project["created_at"] in html
    assert project["folder_name"] in html


def test_project_metadata_update(client, app):
    create_project(client, "Old Project Name", "Old description")
    project = get_latest_project(app)
    token = logged_in_token(client)

    response = client.post(
        f"/projects/{project['id']}/update",
        data={"name": "New Project Name", "description": "New description", "csrf_token": token},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/projects/{project['id']}")

    updated = project_row(app, project["id"])
    assert updated["name"] == "New Project Name"
    assert updated["description"] == "New description"


def test_project_metadata_update_empty_name_rejected(client, app):
    create_project(client, "Solid Name", "Solid description")
    project = get_latest_project(app)
    token = logged_in_token(client)

    response = client.post(
        f"/projects/{project['id']}/update",
        data={"name": "   ", "description": "Changed", "csrf_token": token},
    )
    assert response.status_code == 302
    updated = project_row(app, project["id"])
    assert updated["name"] == "Solid Name"
    assert updated["description"] == "Solid description"


def test_update_preserves_id_created_at_and_folder_name(client, app):
    create_project(client, "Preserve Test", "Details")
    original = get_latest_project(app)
    token = logged_in_token(client)

    client.post(
        f"/projects/{original['id']}/update",
        data={"name": "Preserve Test Modified", "description": "Modified Details", "csrf_token": token},
    )
    updated = project_row(app, original["id"])
    assert updated["id"] == original["id"]
    assert updated["created_at"] == original["created_at"]
    assert updated["folder_name"] == original["folder_name"]


def test_project_status_changes(client, app):
    create_project(client, "Status Project", "Check statuses")
    project = get_latest_project(app)
    token = logged_in_token(client)

    for status in ("Paused", "Archived", "Active"):
        resp = client.post(
            f"/projects/status/{project['id']}",
            data={"status": status, "csrf_token": token},
        )
        assert resp.status_code == 302
        assert project_row(app, project["id"])["status"] == status

    # Invalid status returns 400
    invalid_resp = client.post(
        f"/projects/status/{project['id']}",
        data={"status": "InvalidStatus", "csrf_token": token},
    )
    assert invalid_resp.status_code == 400
    assert project_row(app, project["id"])["status"] == "Active"


def test_missing_project_ids_return_404(client):
    token = logged_in_token(client)
    assert client.get("/projects/99999").status_code == 404
    assert client.post("/projects/99999/update", data={"name": "Ghost", "csrf_token": token}).status_code == 404
    assert client.post("/projects/status/99999", data={"status": "Paused", "csrf_token": token}).status_code == 404
    assert client.post("/projects/delete/99999", data={"csrf_token": token}).status_code == 404
    assert client.get("/projects/99999/folder").status_code == 404


def test_legacy_project_with_null_folder_name_handled_safely(client, app):
    login(client)
    with app.app_context():
        from server.database import get_db

        db = get_db()
        cursor = db.execute(
            "INSERT INTO projects (name, description, status, folder_name) VALUES (?, ?, 'Active', NULL)",
            ("Legacy Retro", "Created before folder_name migration"),
        )
        db.commit()
        legacy_id = cursor.lastrowid

    # List page shows unavailable state without crashing
    list_page = client.get("/projects").get_data(as_text=True)
    assert "Legacy Retro" in list_page
    assert "No folder" in list_page

    # Detail page shows unavailable state without crashing
    detail_page = client.get(f"/projects/{legacy_id}").get_data(as_text=True)
    assert "Legacy Retro" in detail_page
    assert "No folder assigned" in detail_page or "Folder unavailable" in detail_page

    # Folder navigation safely returns 404
    assert client.get(f"/projects/{legacy_id}/folder").status_code == 404

    # No directory was created
    projects_dir = app.config["DATA_ROOT"] / "projects"
    existing_dirs = [p.name for p in projects_dir.iterdir() if p.is_dir()]
    assert f"project-{legacy_id}" not in existing_dirs


def test_folder_navigation_for_valid_project_folder(client, app):
    create_project(client, "File Explorer Project", "Testing folder navigation")
    project = get_latest_project(app)

    folder_dir = app.config["DATA_ROOT"] / "projects" / project["folder_name"]
    (folder_dir / "blueprint.txt").write_bytes(b"Top secret plans")
    (folder_dir / "diagrams").mkdir()

    response = client.get(f"/projects/{project['id']}/folder")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "File Explorer Project" in html
    assert project["folder_name"] in html
    assert "blueprint.txt" in html
    assert "diagrams" in html

    # Verify no absolute system paths leaked
    assert str(app.config["DATA_ROOT"]) not in html


def test_traversal_and_path_boundary_protection_for_folder_navigation(client, app):
    create_project(client, "Traversal Target", "Testing traversal defenses")
    project = get_latest_project(app)

    with app.app_context():
        from server.database import get_db

        db = get_db()
        db.execute("UPDATE projects SET folder_name = ? WHERE id = ?", ("../../photos", project["id"]))
        db.commit()

    response = client.get(f"/projects/{project['id']}/folder")
    assert response.status_code == 400

    # Verify no absolute path leaked in error response
    assert str(app.config["DATA_ROOT"]) not in response.get_data(as_text=True)


def test_project_update_requires_authentication(client, app):
    create_project(client, "Private Project", "Confidential")
    project = get_latest_project(app)

    with client.session_transaction() as session:
        session.clear()

    for path, method in [
        (f"/projects/{project['id']}", "get"),
        (f"/projects/{project['id']}/folder", "get"),
        (f"/projects/{project['id']}/update", "post"),
        (f"/projects/status/{project['id']}", "post"),
        (f"/projects/delete/{project['id']}", "post"),
    ]:
        resp = getattr(client, method)(path)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    assert project_row(app, project["id"])["name"] == "Private Project"


def test_project_update_requires_csrf(client, app):
    create_project(client, "CSRF Protected", "Security test")
    project = get_latest_project(app)
    login(client)

    # Missing CSRF
    assert client.post(f"/projects/{project['id']}/update", data={"name": "Hacked"}).status_code == 400
    assert client.post(f"/projects/status/{project['id']}", data={"status": "Archived"}).status_code == 400
    assert client.post(f"/projects/delete/{project['id']}").status_code == 400

    # Invalid CSRF
    assert client.post(
        f"/projects/{project['id']}/update",
        data={"name": "Hacked", "csrf_token": "bad_token"},
    ).status_code == 400

    assert project_row(app, project["id"])["name"] == "CSRF Protected"


def test_delete_project_retains_folder(client, app):
    create_project(client, "Disposable Project", "Will be deleted")
    project = get_latest_project(app)
    folder_dir = app.config["DATA_ROOT"] / "projects" / project["folder_name"]
    assert folder_dir.is_dir()

    response = client.post(f"/projects/delete/{project['id']}", data={"csrf_token": logged_in_token(client)})
    assert response.status_code == 302
    assert project_row(app, project["id"]) is None
    # Folder directory retained
    assert folder_dir.is_dir()
