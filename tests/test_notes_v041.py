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


def create_note(client, title="Original title", content="Original content"):
    response = client.post(
        "/notes/create",
        data={"title": title, "content": content, "csrf_token": logged_in_token(client)},
    )
    assert response.status_code == 302


def note_row(app, title):
    with app.app_context():
        from server.database import get_db

        return get_db().execute("SELECT * FROM notes WHERE title = ?", (title,)).fetchone()


def test_create_note(client, app):
    create_note(client, "First note", "Created from the form")
    note = note_row(app, "First note")
    assert note["content"] == "Created from the form"


def test_edit_note_updates_timestamp_without_changing_created_at(client, app):
    create_note(client)
    original = note_row(app, "Original title")
    token = logged_in_token(client)
    response = client.post(
        f"/notes/{original['id']}/update",
        data={"title": "Updated title", "content": "Updated content", "csrf_token": token},
    )
    assert response.status_code == 302
    updated = note_row(app, "Updated title")
    assert updated["content"] == "Updated content"
    assert updated["created_at"] == original["created_at"]
    assert updated["updated_at"] != original["updated_at"]


def test_delete_note(client, app):
    create_note(client, "Disposable")
    note = note_row(app, "Disposable")
    response = client.post(f"/notes/delete/{note['id']}", data={"csrf_token": logged_in_token(client)})
    assert response.status_code == 302
    assert note_row(app, "Disposable") is None


def test_search_finds_note_by_title_and_content(client):
    create_note(client, "Shopping list", "Milk and bread")
    create_note(client, "Weekend", "Plan a hiking trip")
    title_page = client.get("/notes?q=shopping").get_data(as_text=True)
    content_page = client.get("/notes?q=hiking").get_data(as_text=True)
    assert "Shopping list" in title_page
    assert "Weekend" not in title_page
    assert "Weekend" in content_page
    assert "Shopping list" not in content_page


def test_empty_search_lists_notes_normally(client):
    create_note(client, "One")
    create_note(client, "Two")
    page = client.get("/notes?q=").get_data(as_text=True)
    assert "One" in page
    assert "Two" in page


def test_nonexistent_notes_return_404(client):
    token = logged_in_token(client)
    assert client.get("/notes/999").status_code == 404
    assert client.post("/notes/999/update", data={"title": "Missing", "content": "", "csrf_token": token}).status_code == 404
    assert client.post("/notes/delete/999", data={"csrf_token": token}).status_code == 404


def test_note_update_requires_authentication_and_csrf(client, app):
    create_note(client, "Protected")
    note = note_row(app, "Protected")
    with client.session_transaction() as session:
        session.clear()
    unauthenticated = client.post(
        f"/notes/{note['id']}/update",
        data={"title": "Changed", "content": "Changed"},
    )
    assert unauthenticated.status_code == 302
    login(client)
    assert client.post(f"/notes/{note['id']}/update", data={"title": "Changed", "content": "Changed"}).status_code == 400
    assert note_row(app, "Protected")["content"] == "Original content"
