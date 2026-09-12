import os

import pytest
from werkzeug.security import generate_password_hash

from server.app import create_app
from server.storage import storage_usage


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "DATA_ROOT": tmp_path / "batcave",
            "DATABASE_PATH": tmp_path / "batcave" / "batcave.db",
            "SECRET_KEY": "test-secret-key",
            "PASSWORD_HASH": generate_password_hash("correct horse battery staple"),
            "MAX_CONTENT_LENGTH": 4096,
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


def token_after_login(client):
    login(client)
    with client.session_transaction() as session:
        return session["csrf_token"]


def make_file(app, relative_path, content=b"content"):
    path = app.config["DATA_ROOT"] / "files" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_breadcrumbs_show_safe_parent_links(client, app):
    (app.config["DATA_ROOT"] / "files" / "reports" / "2026").mkdir(parents=True)
    login(client)
    response = client.get("/files/reports/2026")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'href="/files/reports?' in page
    assert "2026" in page
    assert str(app.config["DATA_ROOT"]) not in page


def test_metadata_and_sorting_keep_folders_distinct(client, app):
    (app.config["DATA_ROOT"] / "files" / "folder").mkdir()
    small = make_file(app, "small.txt", b"x")
    large = make_file(app, "large.txt", b"x" * 100)
    os.utime(small, (1_700_000_100, 1_700_000_100))
    os.utime(large, (1_700_000_000, 1_700_000_000))
    login(client)
    size_page = client.get("/files?sort=size&direction=desc").get_data(as_text=True)
    name_page = client.get("/files?sort=name&direction=asc").get_data(as_text=True)
    modified_page = client.get("/files?sort=modified&direction=desc").get_data(as_text=True)
    assert "Folder" in size_page
    assert "TXT file" in size_page
    assert "Modified" in size_page
    assert size_page.index("folder") < size_page.index("large.txt") < size_page.index("small.txt")
    assert name_page.index("large.txt") < name_page.index("small.txt")
    assert modified_page.index("small.txt") < modified_page.index("large.txt")


def test_search_recurses_only_on_explicit_query_and_returns_relative_paths(client, app):
    make_file(app, "plans/roadmap.md")
    make_file(app, "notes.txt")
    login(client)
    response = client.get("/files?q=road")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "roadmap.md" in page
    assert "plans/roadmap.md" in page
    assert "notes.txt" not in page
    assert str(app.config["DATA_ROOT"]) not in page


def test_move_file_to_existing_folder(client, app):
    make_file(app, "inbox/item.txt", b"move me")
    (app.config["DATA_ROOT"] / "files" / "archive").mkdir()
    token = token_after_login(client)
    response = client.post("/files/move", data={"csrf_token": token, "path": "inbox/item.txt", "destination": "archive"})
    assert response.status_code == 302
    assert not (app.config["DATA_ROOT"] / "files" / "inbox" / "item.txt").exists()
    assert (app.config["DATA_ROOT"] / "files" / "archive" / "item.txt").read_bytes() == b"move me"


def test_move_rejects_unsafe_and_invalid_destinations(client, app):
    make_file(app, "inbox/item.txt")
    token = token_after_login(client)
    assert client.post("/files/move", data={"csrf_token": token, "path": "", "destination": "inbox"}).status_code == 400
    assert client.post("/files/move", data={"csrf_token": token, "path": "inbox/item.txt", "destination": "../../outside"}).status_code == 400
    assert client.post("/files/move", data={"csrf_token": token, "path": "inbox/item.txt", "destination": "missing"}).status_code == 400


def test_move_rejects_folder_descendants_and_duplicate_destinations(client, app):
    (app.config["DATA_ROOT"] / "files" / "parent" / "child").mkdir(parents=True)
    make_file(app, "inbox/same.txt", b"source")
    make_file(app, "archive/same.txt", b"destination")
    token = token_after_login(client)
    descendant = client.post("/files/move", data={"csrf_token": token, "path": "parent", "destination": "parent/child"})
    assert descendant.status_code == 400
    duplicate = client.post("/files/move", data={"csrf_token": token, "path": "inbox/same.txt", "destination": "archive"})
    assert duplicate.status_code == 302
    assert (app.config["DATA_ROOT"] / "files" / "inbox" / "same.txt").exists()
    assert (app.config["DATA_ROOT"] / "files" / "archive" / "same.txt").read_bytes() == b"destination"


def test_storage_usage_is_rendered_without_tree_size_scan(client, app):
    login(client)
    expected = storage_usage(app.config["DATA_ROOT"] / "files")
    page = client.get("/files").get_data(as_text=True)
    assert "Used" in page and "Free" in page and "Total" in page
    assert expected["used"] in page
    assert expected["free"] in page
    assert expected["total"] in page


def test_files_move_stays_protected_by_authentication_and_csrf(client, app):
    make_file(app, "item.txt")
    (app.config["DATA_ROOT"] / "files" / "target").mkdir()
    assert client.post("/files/move", data={"path": "item.txt", "destination": "target"}).status_code == 302
    login(client)
    assert client.post("/files/move", data={"path": "item.txt", "destination": "target"}).status_code == 400
    assert (app.config["DATA_ROOT"] / "files" / "item.txt").exists()
