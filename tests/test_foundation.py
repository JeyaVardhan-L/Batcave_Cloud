from io import BytesIO
import re

import pytest
from PIL import Image
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
            "MAX_CONTENT_LENGTH": 1024,
        }
    )
    yield application
    # Be explicit about closing any database connection associated with a test
    # app context before pytest removes its Windows temporary directory.
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


def png_file(name="photo.png"):
    image = Image.new("RGB", (2, 2), "purple")
    data = BytesIO()
    image.save(data, format="PNG")
    data.seek(0)
    return data, name


def test_protected_routes_redirect_to_login(client):
    for path in ("/", "/files", "/photos", "/notes", "/ideas", "/projects", "/backups"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_login_and_logout(client):
    token = csrf(client)
    assert client.post("/login", data={"password": "wrong", "csrf_token": token}).status_code == 200
    assert login(client).status_code == 302
    assert client.get("/").status_code == 200
    response = client.post("/logout", data={"csrf_token": authenticated_csrf(client)})
    assert response.status_code == 302
    assert client.get("/").status_code == 302


def test_posts_require_csrf(client):
    login(client)
    assert client.post("/notes/create", data={"title": "No token"}).status_code == 400


def test_rendered_mutating_forms_include_csrf_tokens(client):
    login(client)
    for path in ("/files", "/photos", "/notes", "/ideas", "/projects"):
        response = client.get(path)
        forms = re.findall(r"<form\b.*?</form>", response.get_data(as_text=True), flags=re.DOTALL)
        assert forms
        assert all('name="csrf_token"' in form for form in forms)


def test_notes_ideas_and_projects_can_be_created(client, app):
    token = authenticated_csrf(client)
    assert client.post("/notes/create", data={"title": "Note", "content": "Body", "csrf_token": token}).status_code == 302
    assert client.post("/ideas/create", data={"content": "Idea", "csrf_token": token}).status_code == 302
    assert client.post("/projects/create", data={"name": "Project", "description": "Desc", "csrf_token": token}).status_code == 302
    with app.app_context():
        from server.database import get_db
        project = get_db().execute("SELECT folder_name FROM projects").fetchone()
        assert project["folder_name"] == "project-1"
    assert (app.config["DATA_ROOT"] / "projects" / "project-1").is_dir()


def test_files_root_cannot_be_deleted_or_renamed(client, app):
    token = authenticated_csrf(client)
    assert client.post("/files/delete", data={"path": "", "csrf_token": token}).status_code == 400
    assert client.post("/files/rename", data={"path": "", "new_name": "moved", "csrf_token": token}).status_code == 400
    assert (app.config["DATA_ROOT"] / "files").is_dir()


def test_path_traversal_is_blocked(client):
    login(client)
    assert client.get("/files/%2e%2e/%2e%2e").status_code == 400


def test_duplicate_upload_does_not_overwrite(client, app):
    token = authenticated_csrf(client)
    first = client.post("/files/upload", data={"csrf_token": token, "path": "", "file": (BytesIO(b"first"), "same.txt")})
    assert first.status_code == 302
    second = client.post("/files/upload", data={"csrf_token": token, "path": "", "file": (BytesIO(b"second"), "same.txt")})
    assert second.status_code == 302
    assert (app.config["DATA_ROOT"] / "files" / "same.txt").read_bytes() == b"first"
    assert client.get("/files").status_code == 200


def test_upload_size_limit(client):
    token = authenticated_csrf(client)
    response = client.post("/files/upload", data={"csrf_token": token, "path": "", "file": (BytesIO(b"x" * 2048), "large.bin")})
    assert response.status_code == 413


def test_photo_validation_and_upload(client, app):
    token = authenticated_csrf(client)
    invalid = client.post("/photos/upload", data={"csrf_token": token, "photo": (BytesIO(b"not an image"), "fake.png")})
    assert invalid.status_code == 302
    assert not (app.config["DATA_ROOT"] / "photos" / "fake.png").exists()
    image, name = png_file()
    valid = client.post("/photos/upload", data={"csrf_token": token, "photo": (image, name)})
    assert valid.status_code == 302
    assert (app.config["DATA_ROOT"] / "photos" / "photo.png").exists()


def test_download_forces_attachment_and_security_headers(client, app):
    token = authenticated_csrf(client)
    client.post("/files/upload", data={"csrf_token": token, "path": "", "file": (BytesIO(b"<script>"), "page.html")})
    with client.get("/files/open/page.html") as response:
        assert response.status_code == 200
        assert "attachment" in response.headers["Content-Disposition"]
        assert response.headers["X-Content-Type-Options"] == "nosniff"
