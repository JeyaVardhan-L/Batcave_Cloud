"""Authenticated application routes."""

from __future__ import annotations

from pathlib import Path

from flask import abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for

try:
    from .database import get_db
    from .storage import InvalidPathError, clean_name, file_info, is_photo_filename, resolve_path, save_new_upload, validate_photo
except ImportError:  # pragma: no cover - direct-script deployment path
    from database import get_db
    from storage import InvalidPathError, clean_name, file_info, is_photo_filename, resolve_path, save_new_upload, validate_photo


def _root(name: str) -> Path:
    return Path(current_app.config["DATA_ROOT"]) / name


def _safe_path(root: Path, value: str, *, allow_root: bool = True) -> Path:
    try:
        return resolve_path(root, value, allow_root=allow_root)
    except InvalidPathError as error:
        abort(400, str(error))


def _parent_path(path: Path, root: Path) -> str:
    parent = path.parent.relative_to(root).as_posix()
    return "" if parent == "." else parent


def register_routes(app) -> None:
    @app.route("/")
    def dashboard():
        files_root, photos_root = _root("files"), _root("photos")
        db = get_db()
        return render_template(
            "dashboard.html",
            file_count=sum(1 for path in files_root.rglob("*") if path.is_file()),
            photo_count=sum(1 for path in photos_root.rglob("*") if path.is_file()),
            note_count=db.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
            idea_count=db.execute("SELECT COUNT(*) FROM ideas").fetchone()[0],
            project_count=db.execute("SELECT COUNT(*) FROM projects WHERE status = 'Active'").fetchone()[0],
        )

    @app.route("/files")
    @app.route("/files/<path:subpath>")
    def files(subpath=""):
        root = _root("files")
        current_dir = _safe_path(root, subpath)
        if not current_dir.exists():
            abort(404)
        if not current_dir.is_dir():
            abort(400, "Not a directory.")
        folders, files_list = [], []
        for item in current_dir.iterdir():
            if item.is_dir():
                folders.append({"name": item.name, "path": item.relative_to(root).as_posix()})
            elif item.is_file():
                files_list.append(file_info(item, root))
        folders.sort(key=lambda item: item["name"].lower())
        files_list.sort(key=lambda item: item["name"].lower())
        parent_path = None if not subpath else Path(subpath).parent.as_posix()
        return render_template("files.html", current_path=subpath, folders=folders, files=files_list,
                               parent_path="" if parent_path == "." else parent_path)

    @app.post("/files/upload")
    def upload_file():
        relative_path = request.form.get("path", "")
        target_dir = _safe_path(_root("files"), relative_path)
        if not target_dir.is_dir():
            abort(400, "Target directory does not exist.")
        uploaded = request.files.get("file")
        filename = clean_name(uploaded.filename) if uploaded and uploaded.filename else ""
        if not filename:
            flash("Please select a valid file.")
        else:
            try:
                save_new_upload(uploaded, target_dir, filename)
                flash(f"Uploaded {filename}")
            except FileExistsError as error:
                flash(str(error))
        return redirect(url_for("files", subpath=relative_path))

    @app.post("/files/mkdir")
    def create_folder():
        relative_path = request.form.get("path", "")
        parent = _safe_path(_root("files"), relative_path)
        if not parent.is_dir():
            abort(400, "Target directory does not exist.")
        name = clean_name(request.form.get("folder_name", ""))
        if not name:
            flash("Folder name is invalid.")
        elif (parent / name).exists():
            flash("That folder already exists.")
        else:
            (parent / name).mkdir()
            flash(f"Created folder {name}")
        return redirect(url_for("files", subpath=relative_path))

    @app.post("/files/rename")
    def rename_file():
        root = _root("files")
        old = _safe_path(root, request.form.get("path", ""), allow_root=False)
        if not old.exists():
            abort(404)
        name = clean_name(request.form.get("new_name", ""))
        parent_path = _parent_path(old, root)
        if not name:
            flash("New name is invalid.")
        elif (old.parent / name).exists():
            flash("A file or folder with that name already exists.")
        else:
            old.rename(old.parent / name)
            flash(f"Renamed to {name}")
        return redirect(url_for("files", subpath=parent_path))

    @app.post("/files/delete")
    def delete_file():
        root = _root("files")
        target = _safe_path(root, request.form.get("path", ""), allow_root=False)
        if not target.exists():
            abort(404)
        parent_path = _parent_path(target, root)
        if target.is_dir():
            try:
                target.rmdir()
            except OSError:
                flash("Folder is not empty.")
                return redirect(url_for("files", subpath=parent_path))
        else:
            target.unlink()
        flash(f"Deleted {target.name}")
        return redirect(url_for("files", subpath=parent_path))

    @app.route("/files/download/<path:filename>")
    @app.route("/files/open/<path:filename>", endpoint="open_file")
    def download_file(filename):
        root = _root("files")
        path = _safe_path(root, filename, allow_root=False)
        if not path.is_file():
            abort(404)
        return send_from_directory(root, filename, as_attachment=True, download_name=path.name)

    @app.route("/notes")
    def notes():
        return render_template("notes.html", notes=get_db().execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall())

    @app.post("/notes/create")
    def create_note():
        title, content = request.form.get("title", "").strip(), request.form.get("content", "").strip()
        if not title:
            flash("Note title is required.")
        else:
            db = get_db()
            db.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
            db.commit()
            flash("Note created.")
        return redirect(url_for("notes"))

    @app.post("/notes/delete/<int:note_id>")
    def delete_note(note_id):
        db = get_db()
        db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        db.commit()
        flash("Note deleted.")
        return redirect(url_for("notes"))

    @app.route("/ideas")
    def ideas():
        return render_template("ideas.html", ideas=get_db().execute("SELECT * FROM ideas ORDER BY created_at DESC").fetchall())

    @app.post("/ideas/create")
    def create_idea():
        content = request.form.get("content", "").strip()
        if not content:
            flash("Idea cannot be empty.")
        else:
            db = get_db()
            db.execute("INSERT INTO ideas (content) VALUES (?)", (content,))
            db.commit()
            flash("Idea captured.")
        return redirect(url_for("ideas"))

    @app.post("/ideas/delete/<int:idea_id>")
    def delete_idea(idea_id):
        db = get_db()
        db.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
        db.commit()
        flash("Idea deleted.")
        return redirect(url_for("ideas"))

    @app.route("/projects")
    def projects():
        return render_template("projects.html", projects=get_db().execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall())

    @app.post("/projects/create")
    def create_project():
        name, description = request.form.get("name", "").strip(), request.form.get("description", "").strip()
        if not name:
            flash("Project name is required.")
            return redirect(url_for("projects"))
        db = get_db()
        cursor = db.execute("INSERT INTO projects (name, description, status) VALUES (?, ?, 'Active')", (name, description))
        db.commit()
        folder_name = f"project-{cursor.lastrowid}"
        try:
            (_root("projects") / folder_name).mkdir()
            db.execute("UPDATE projects SET folder_name = ? WHERE id = ?", (folder_name, cursor.lastrowid))
            db.commit()
            flash("Project created.")
        except OSError:
            current_app.logger.exception("Could not create project directory for project %s", cursor.lastrowid)
            flash("Project record was created, but its folder could not be created.")
        return redirect(url_for("projects"))

    @app.post("/projects/status/<int:project_id>")
    def change_project_status(project_id):
        status = request.form.get("status", "Active")
        if status not in {"Active", "Paused", "Archived"}:
            abort(400)
        db = get_db()
        db.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
        db.commit()
        return redirect(url_for("projects"))

    @app.post("/projects/delete/<int:project_id>")
    def delete_project(project_id):
        db = get_db()
        db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        db.commit()
        flash("Project deleted. Its directory was retained to avoid deleting project files.")
        return redirect(url_for("projects"))

    @app.route("/photos")
    def photos():
        root = _root("photos")
        photos_list = [{"name": photo.name, "path": photo.relative_to(root).as_posix()} for photo in root.rglob("*")
                       if photo.is_file() and is_photo_filename(photo.name)]
        photos_list.sort(key=lambda item: item["name"].lower())
        return render_template("photos.html", photos=photos_list)

    @app.post("/photos/upload")
    def upload_photo():
        uploaded = request.files.get("photo")
        filename = clean_name(uploaded.filename) if uploaded and uploaded.filename else ""
        if not filename:
            flash("Please select a valid photo.")
        else:
            try:
                validate_photo(uploaded, filename)
                save_new_upload(uploaded, _root("photos"), filename)
                flash(f"Uploaded {filename}")
            except (ValueError, FileExistsError) as error:
                flash(str(error))
        return redirect(url_for("photos"))

    @app.route("/photos/view/<path:filename>")
    def view_photo(filename):
        if not is_photo_filename(filename):
            abort(404)
        root = _root("photos")
        path = _safe_path(root, filename, allow_root=False)
        if not path.is_file():
            abort(404)
        return send_from_directory(root, filename)

    @app.route("/backups")
    def backups():
        return render_template("backups.html", backup_count=sum(1 for path in _root("backups").rglob("*") if path.is_file()))
