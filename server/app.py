from pathlib import Path
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from database import get_connection, init_database


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BATCAVE_ROOT = Path.home() / "storage" / "shared" / "BatCave"

FILES_ROOT = BATCAVE_ROOT / "files"
PHOTOS_ROOT = BATCAVE_ROOT / "photos"
NOTES_ROOT = BATCAVE_ROOT / "notes"
IDEAS_ROOT = BATCAVE_ROOT / "ideas"
PROJECTS_ROOT = BATCAVE_ROOT / "projects"
BACKUPS_ROOT = BATCAVE_ROOT / "backups"
ARCHIVE_ROOT = BATCAVE_ROOT / "archive"

DATABASE_PATH = BATCAVE_ROOT / "batcave.db"


# --------------------------------------------------
# Flask
# --------------------------------------------------

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "web" / "templates"),
    static_folder=str(PROJECT_ROOT / "web" / "static"),
)

app.secret_key = "batcave-development-key"


# --------------------------------------------------
# Initial setup
# --------------------------------------------------

for folder in [
    FILES_ROOT,
    PHOTOS_ROOT,
    NOTES_ROOT,
    IDEAS_ROOT,
    PROJECTS_ROOT,
    BACKUPS_ROOT,
    ARCHIVE_ROOT,
]:
    folder.mkdir(parents=True, exist_ok=True)

init_database(DATABASE_PATH)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def get_db():
    return get_connection(DATABASE_PATH)


def safe_relative_path(root: Path, relative_path: str) -> Path:
    """
    Convert a user-provided relative path into a safe filesystem path.

    The resulting path must remain inside root.
    """

    relative_path = relative_path.strip().strip("/")

    candidate = (root / relative_path).resolve()
    root_resolved = root.resolve()

    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        abort(400, "Invalid path.")

    return candidate


def format_size(size):
    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"

    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"

    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def file_info(path: Path, relative_to: Path):
    stat = path.stat()

    return {
        "name": path.name,
        "path": path.relative_to(relative_to).as_posix(),
        "size": format_size(stat.st_size),
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
            "%Y-%m-%d %H:%M"
        ),
    }


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@app.route("/")
def dashboard():
    file_count = sum(1 for p in FILES_ROOT.rglob("*") if p.is_file())
    photo_count = sum(1 for p in PHOTOS_ROOT.rglob("*") if p.is_file())

    connection = get_db()

    note_count = connection.execute(
        "SELECT COUNT(*) FROM notes"
    ).fetchone()[0]

    idea_count = connection.execute(
        "SELECT COUNT(*) FROM ideas"
    ).fetchone()[0]

    project_count = connection.execute(
        "SELECT COUNT(*) FROM projects WHERE status = 'Active'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "dashboard.html",
        file_count=file_count,
        photo_count=photo_count,
        note_count=note_count,
        idea_count=idea_count,
        project_count=project_count,
    )


# --------------------------------------------------
# Files
# --------------------------------------------------

@app.route("/files")
@app.route("/files/<path:subpath>")
def files(subpath=""):
    current_dir = safe_relative_path(FILES_ROOT, subpath)

    if not current_dir.exists():
        abort(404)

    if not current_dir.is_dir():
        abort(400, "Not a directory.")

    folders = []
    files_list = []

    for item in current_dir.iterdir():
        if item.is_dir():
            folders.append(
                {
                    "name": item.name,
                    "path": item.relative_to(FILES_ROOT).as_posix(),
                }
            )

        elif item.is_file():
            files_list.append(
                file_info(item, FILES_ROOT)
            )

    folders.sort(key=lambda item: item["name"].lower())
    files_list.sort(key=lambda item: item["name"].lower())

    parent_path = None

    if subpath:
        parent = Path(subpath).parent.as_posix()

        if parent == ".":
            parent = ""

        parent_path = parent

    return render_template(
        "files.html",
        current_path=subpath,
        folders=folders,
        files=files_list,
        parent_path=parent_path,
    )


@app.post("/files/upload")
def upload_file():
    relative_path = request.form.get("path", "")

    target_dir = safe_relative_path(
        FILES_ROOT,
        relative_path,
    )

    if not target_dir.exists() or not target_dir.is_dir():
        abort(400, "Target directory does not exist.")

    uploaded = request.files.get("file")

    if not uploaded or not uploaded.filename:
        flash("Please select a file.")
        return redirect(url_for("files", subpath=relative_path))

    filename = secure_filename(uploaded.filename)

    if not filename:
        flash("Invalid filename.")
        return redirect(url_for("files", subpath=relative_path))

    destination = target_dir / filename

    uploaded.save(destination)

    flash(f"Uploaded {filename}")

    return redirect(url_for("files", subpath=relative_path))


@app.post("/files/mkdir")
def create_folder():
    relative_path = request.form.get("path", "")
    folder_name = request.form.get("folder_name", "").strip()

    if not folder_name:
        flash("Folder name cannot be empty.")
        return redirect(url_for("files", subpath=relative_path))

    safe_name = secure_filename(folder_name)

    if not safe_name:
        flash("Invalid folder name.")
        return redirect(url_for("files", subpath=relative_path))

    parent = safe_relative_path(FILES_ROOT, relative_path)
    new_folder = parent / safe_name

    if new_folder.exists():
        flash("That folder already exists.")
    else:
        new_folder.mkdir()
        flash(f"Created folder {safe_name}")

    return redirect(url_for("files", subpath=relative_path))


@app.post("/files/rename")
def rename_file():
    old_path = request.form.get("path", "")
    new_name = request.form.get("new_name", "").strip()

    if not new_name:
        flash("New name cannot be empty.")
        return redirect(url_for("files"))

    old = safe_relative_path(FILES_ROOT, old_path)

    if not old.exists():
        abort(404)

    safe_name = secure_filename(new_name)

    if not safe_name:
        flash("Invalid filename.")
        return redirect(url_for("files", subpath=old.parent.relative_to(FILES_ROOT)))

    new_path = old.parent / safe_name

    if new_path.exists():
        flash("A file or folder with that name already exists.")
    else:
        old.rename(new_path)
        flash(f"Renamed to {safe_name}")

    parent = old.parent.relative_to(FILES_ROOT).as_posix()

    if parent == ".":
        parent = ""

    return redirect(url_for("files", subpath=parent))


@app.post("/files/delete")
def delete_file():
    relative_path = request.form.get("path", "")

    target = safe_relative_path(
        FILES_ROOT,
        relative_path,
    )

    if not target.exists():
        abort(404)

    if target.is_dir():
        try:
            target.rmdir()
        except OSError:
            flash("Folder is not empty.")
            return redirect(url_for("files", subpath=target.parent.relative_to(FILES_ROOT)))
    else:
        target.unlink()

    parent = target.parent.relative_to(FILES_ROOT).as_posix()

    if parent == ".":
        parent = ""

    flash(f"Deleted {target.name}")

    return redirect(url_for("files", subpath=parent))


@app.route("/files/download/<path:filename>")
def download_file(filename):
    target = safe_relative_path(FILES_ROOT, filename)

    if not target.exists() or not target.is_file():
        abort(404)

    relative_parent = target.parent.relative_to(FILES_ROOT)

    return send_from_directory(
        FILES_ROOT / relative_parent,
        target.name,
        as_attachment=True,
    )


@app.route("/files/open/<path:filename>")
def open_file(filename):
    target = safe_relative_path(FILES_ROOT, filename)

    if not target.exists() or not target.is_file():
        abort(404)

    relative_parent = target.parent.relative_to(FILES_ROOT)

    return send_from_directory(
        FILES_ROOT / relative_parent,
        target.name,
    )


# --------------------------------------------------
# Notes
# --------------------------------------------------

@app.route("/notes")
def notes():
    connection = get_db()

    notes_list = connection.execute(
        """
        SELECT *
        FROM notes
        ORDER BY updated_at DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "notes.html",
        notes=notes_list,
    )


@app.post("/notes/create")
def create_note():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()

    if not title:
        flash("Note title is required.")
        return redirect(url_for("notes"))

    connection = get_db()

    connection.execute(
        """
        INSERT INTO notes (title, content)
        VALUES (?, ?)
        """,
        (title, content),
    )

    connection.commit()
    connection.close()

    flash("Note created.")

    return redirect(url_for("notes"))


@app.post("/notes/delete/<int:note_id>")
def delete_note(note_id):
    connection = get_db()

    connection.execute(
        "DELETE FROM notes WHERE id = ?",
        (note_id,),
    )

    connection.commit()
    connection.close()

    flash("Note deleted.")

    return redirect(url_for("notes"))


# --------------------------------------------------
# Ideas
# --------------------------------------------------

@app.route("/ideas")
def ideas():
    connection = get_db()

    ideas_list = connection.execute(
        """
        SELECT *
        FROM ideas
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "ideas.html",
        ideas=ideas_list,
    )


@app.post("/ideas/create")
def create_idea():
    content = request.form.get("content", "").strip()

    if not content:
        flash("Idea cannot be empty.")
        return redirect(url_for("ideas"))

    connection = get_db()

    connection.execute(
        """
        INSERT INTO ideas (content)
        VALUES (?)
        """,
        (content,),
    )

    connection.commit()
    connection.close()

    flash("Idea captured.")

    return redirect(url_for("ideas"))


@app.post("/ideas/delete/<int:idea_id>")
def delete_idea(idea_id):
    connection = get_db()

    connection.execute(
        "DELETE FROM ideas WHERE id = ?",
        (idea_id,),
    )

    connection.commit()
    connection.close()

    flash("Idea deleted.")

    return redirect(url_for("ideas"))


# --------------------------------------------------
# Projects
# --------------------------------------------------

@app.route("/projects")
def projects():
    connection = get_db()

    projects_list = connection.execute(
        """
        SELECT *
        FROM projects
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "projects.html",
        projects=projects_list,
    )


@app.post("/projects/create")
def create_project():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Project name is required.")
        return redirect(url_for("projects"))

    connection = get_db()

    connection.execute(
        """
        INSERT INTO projects (name, description, status)
        VALUES (?, ?, 'Active')
        """,
        (name, description),
    )

    connection.commit()
    connection.close()

    project_folder = PROJECTS_ROOT / secure_filename(name)

    if project_folder.name:
        project_folder.mkdir(exist_ok=True)

    flash("Project created.")

    return redirect(url_for("projects"))


@app.post("/projects/status/<int:project_id>")
def change_project_status(project_id):
    status = request.form.get("status", "Active")

    allowed = {
        "Active",
        "Paused",
        "Archived",
    }

    if status not in allowed:
        abort(400)

    connection = get_db()

    connection.execute(
        """
        UPDATE projects
        SET status = ?
        WHERE id = ?
        """,
        (status, project_id),
    )

    connection.commit()
    connection.close()

    return redirect(url_for("projects"))


@app.post("/projects/delete/<int:project_id>")
def delete_project(project_id):
    connection = get_db()

    connection.execute(
        "DELETE FROM projects WHERE id = ?",
        (project_id,),
    )

    connection.commit()
    connection.close()

    flash("Project deleted.")

    return redirect(url_for("projects"))


# --------------------------------------------------
# Photos
# --------------------------------------------------

@app.route("/photos")
def photos():
    photos_list = []

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
    }

    for photo in PHOTOS_ROOT.rglob("*"):
        if (
            photo.is_file()
            and photo.suffix.lower() in allowed_extensions
        ):
            photos_list.append(
                {
                    "name": photo.name,
                    "path": photo.relative_to(PHOTOS_ROOT).as_posix(),
                }
            )

    photos_list.sort(
        key=lambda item: item["name"].lower()
    )

    return render_template(
        "photos.html",
        photos=photos_list,
    )


@app.post("/photos/upload")
def upload_photo():
    uploaded = request.files.get("photo")

    if not uploaded or not uploaded.filename:
        flash("Please select a photo.")
        return redirect(url_for("photos"))

    filename = secure_filename(uploaded.filename)

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
    }

    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        flash("That file type is not supported as a photo.")
        return redirect(url_for("photos"))

    uploaded.save(PHOTOS_ROOT / filename)

    flash(f"Uploaded {filename}")

    return redirect(url_for("photos"))


@app.route("/photos/view/<path:filename>")
def view_photo(filename):
    target = safe_relative_path(PHOTOS_ROOT, filename)

    if not target.exists() or not target.is_file():
        abort(404)

    relative_parent = target.parent.relative_to(PHOTOS_ROOT)

    return send_from_directory(
        relative_parent,
        target.name,
        directory=PHOTOS_ROOT,
    )


# --------------------------------------------------
# Backups
# --------------------------------------------------

@app.route("/backups")
def backups():
    backup_count = sum(
        1
        for p in BACKUPS_ROOT.rglob("*")
        if p.is_file()
    )

    return render_template(
        "backups.html",
        backup_count=backup_count,
    )


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False,
    )