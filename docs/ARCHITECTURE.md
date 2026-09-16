# Batcave Cloud — System Architecture

This document describes the technical design, module responsibilities, request lifecycle, data model, and filesystem layout of Batcave Cloud (v0.5.1).

---

## 1. Architectural Overview

Batcave Cloud is a self-hosted personal cloud workspace built on Python and Flask, designed to run as a single-user system on local area networks (LAN) or edge devices (such as Android devices running Termux).

The system separates concerns into discrete layers:
- **Presentation & Web Assets**: Jinja2 templates and vanilla CSS.
- **Application Factory & Security**: Global request gating, session management, CSRF validation, and security headers.
- **Routing & Controllers**: Authenticated endpoints for Files, Photos, Notes, Ideas, and Projects.
- **Storage Layer**: Path traversal defense, disk quota inspection, atomic upload handling, and image verification.
- **Database Layer**: SQLite with Write-Ahead Logging (WAL), connection lifecycle management, and additive schema migrations.
- **Configuration & CLI**: Environment variable parsing, private config file loading, and credential generation.

```text
+-------------------------------------------------------------+
|                      Client Browser                         |
+-------------------------------------------------------------+
                               |
                               | HTTP (LAN)
                               v
+-------------------------------------------------------------+
|                     Flask Application                       |
|  - server/app.py (Factory, before_request, after_request)   |
|  - server/config.py (Env loading & security validation)     |
|  - server/auth.py (Password verification & CSRF checks)     |
+-------------------------------------------------------------+
        |                                             |
        v                                             v
+-----------------------+                 +---------------------------+
|    Route Handlers     |                 |       HTML Rendering      |
|   (server/routes.py)  |                 |  - web/templates/*.html   |
+-----------------------+                 |  - web/static/style.css   |
     |             |                      +---------------------------+
     v             v
+-----------+   +-----------------------------------------------------+
|  SQLite   |   |                   Storage Layer                     |
| Database  |   |                (server/storage.py)                  |
| (WAL mode)|   +-----------------------------------------------------+
+-----------+                              |
                                           v
                        +-------------------------------------+
                        |          Batcave Data Root          |
                        |      (Filesystem Directories)       |
                        |  files/ photos/ notes/ ideas/       |
                        |  projects/ backups/ archive/        |
                        +-------------------------------------+
```

---

## 2. Component Responsibilities

### [`server/app.py`](../server/app.py) — Application Factory & Pipeline Security
- **Factory Pattern (`create_app`)**: Initializes the Flask application with explicit template and static paths, applies configuration, validates secrets, ensures root storage directories exist, and initializes the SQLite database.
- **Directory Bootstrapping**: Automatically creates the 7 core subdirectories (`files`, `photos`, `notes`, `ideas`, `projects`, `backups`, `archive`) inside `DATA_ROOT` on startup.
- **Global Authentication Gate (`@app.before_request`)**:
  - Gated endpoints: All endpoints except `static` and `login` require `session["authenticated"] == True`. Unauthenticated requests are redirected to `/login?next=<path>`.
  - Next URL validation: `_safe_next_url()` ensures redirect targets are relative paths, preventing open redirect vulnerabilities.
- **Global CSRF Gate (`@app.before_request`)**:
  - Intercepts all incoming `POST` requests and validates `request.form.get("csrf_token")` against `session.get("csrf_token")` using constant-time comparison (`secrets.compare_digest`).
  - Aborts with HTTP 400 if the token is invalid or missing.
- **Security Headers (`@app.after_request`)**:
  - Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, and a restrictive `Permissions-Policy`.
  - Implements a restrictive `Content-Security-Policy`:
    ```text
    default-src 'self'; img-src 'self' data:; style-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'
    ```
  - Appends `Cache-Control: no-store` on non-static responses to prevent caching authenticated content on shared devices.
- **Central Error Handling**: Provides user-friendly error views for HTTP 400, 403, 404, 413 (File Too Large), and 500.

### [`server/config.py`](../server/config.py) — Configuration Management
- **Automatic Configuration Discovery (`get_default_config_path`, `find_default_config_path`)**: Automatically discovers configuration files at `$XDG_CONFIG_HOME/batcave-cloud/batcave.env` or `~/.config/batcave-cloud/batcave.env` when `BATCAVE_CONFIG_FILE` is not explicitly exported.
- **Environment File Loader (`load_environment_file`)**: Loads simple `KEY=value` configuration files without external dependencies. Supports both explicit paths (where missing file triggers an error) and auto-discovered default paths.
- **Configuration Builder (`build_config`)**:
  - `DATA_ROOT`: Storage root directory (defaults to `/storage/emulated/0/BatCave`).
  - `DATABASE_PATH`: Points to `DATA_ROOT / "batcave.db"`.
  - `SECRET_KEY`: High-entropy random key for signing cookies.
  - `PASSWORD_HASH`: Werkzeug password hash string.
  - `MAX_CONTENT_LENGTH`: Maximum payload size in bytes (defaults to 25 MB).
  - `HOST`: Server bind address (defaults to `0.0.0.0`).
  - `PORT`: Server port (defaults to `8080`).
  - `SESSION_COOKIE_HTTPONLY`: Always `True`.
  - `SESSION_COOKIE_SAMESITE`: Configured to `Lax`.
  - `SESSION_COOKIE_SECURE`: Configurable boolean (set `True` when behind HTTPS).
- **Security Validation (`validate_security_config`)**: Refuses to boot the server if `SECRET_KEY` or `PASSWORD_HASH` is missing or empty. Never silently generates credentials; provides clear setup guidance.

### [`server/auth.py`](../server/auth.py) — Authentication & CSRF
- **Password Verification (`verify_password`)**: Verifies passwords against `PASSWORD_HASH` using `werkzeug.security.check_password_hash`.
- **CSRF Token Generation & Verification**:
  - `csrf_token()`: Generates and caches a 32-byte URL-safe cryptographic token in the session.
  - `valid_csrf_token()`: Validates token using `secrets.compare_digest`.
  - `csrf_protect`: Decorator for explicit endpoint protection (complementing global middleware).

### [`server/storage.py`](../server/storage.py) — Safe Storage & Media Handling
- **Path Confinement (`resolve_path`)**:
  - Canonicalizes both root and target paths using `Path.resolve()`.
  - Enforces that target paths are strictly within root via `Path.relative_to()`.
  - Prevents path traversal (`../../`) and access to system files outside the storage sandbox.
  - Supports `allow_root=False` to prevent renaming, deleting, or overwriting root directories.
- **Filename Sanitization (`clean_name`)**: Strips unsafe characters and path delimiters using Werkzeug's `secure_filename`.
- **Atomic File Creation (`save_new_upload`)**:
  - Opens destination files with exclusive binary creation mode (`xb`).
  - Throws `FileExistsError` instead of overwriting existing files.
  - Cleans up partial files if upload streaming fails midway.
- **Photo Validation (`validate_photo`)**:
  - Enforces allowed image extensions (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`).
  - Validates file content using Pillow (`Image.open()` and `Image.verify()`).
  - Ensures actual image header format matches the file extension.
  - Defends against image bombs via `Image.MAX_IMAGE_PIXELS = 30_000_000`.
- **Metadata & Disk Usage**:
  - Formats file sizes into human-readable units (`B`, `KB`, `MB`, `GB`).
  - `storage_usage()` computes filesystem capacity via `shutil.disk_usage()` in $O(1)$ time without recursive directory scans.

### [`server/database.py`](../server/database.py) — SQLite & Schema Migrations
- **Connection Management**:
  - SQLite with `timeout=10` and `PRAGMA busy_timeout = 10000`.
  - Configures `PRAGMA foreign_keys = ON` and `row_factory = sqlite3.Row`.
  - Enables Write-Ahead Logging (`PRAGMA journal_mode = WAL`) on initialization for concurrent read performance.
- **Additive Migrations (`PRAGMA user_version`)**:
  - Tracks schema version via SQLite's internal `user_version`.
  - Migration 1: Creates tables `notes`, `ideas`, and `projects`.
  - Migration 2: Adds `folder_name TEXT` column to `projects` table safely.

### [`server/routes.py`](../server/routes.py) — Application Controllers
- **Dashboard (`/`)**: Main Command Center aggregating storage capacity summary via `storage_usage`, real workspace counts (Notes, Ideas, Projects), quick action links to existing workflows, and recent items (Notes, Ideas, Active Projects) in $O(1)$ without recursive directory traversal.
- **Files (`/files`, `/files/<subpath>`)**: Directory navigation, clickable breadcrumbs, file sorting (name, size, date), recursive search, upload, directory creation, rename, move (with descendant/cycle prevention), download, and safe open.
- **Notes (`/notes`, `/notes/<id>`)**: Notes list, note creation, note editing/updating (with automatic `updated_at` timestamps), deletion, and search (title/content) ordered by most recently updated.
- **Ideas (`/ideas`, `/ideas/<id>`)**: Quick-capture idea list, idea creation, editing/updating (preserving `created_at`), deletion, and search ordered newest-first.
- **Projects (`/projects`, `/projects/<id>`)**: Project dashboard, creation (allocating isolated `project-<id>` directory), detail/edit view, status updates (`Active`, `Paused`, `Archived`), project folder exploration, and deletion (safely retaining the filesystem directory).
- **Photos (`/photos`, `/photos/upload`, `/photos/view/<filename>`)**: Photo grid, verified image uploads, and safe inline image delivery.
- **Backups (`/backups`)**: View backup statistics.

### [`server/manage.py`](../server/manage.py) — Local Management CLI
- Provides `create-config [--output <path>]` command:
  - Prompts securely for password using `getpass`.
  - Generates high-entropy secret key (`secrets.token_urlsafe(48)`).
  - Hashes password with Werkzeug.
  - Writes private config file (defaulting to `~/.config/batcave-cloud/batcave.env`) and sets file permissions to `0600` on POSIX systems.

---

## 3. Request Lifecycle

```text
1. Browser sends HTTP Request
   |
2. server/app.py -> require_login_and_csrf()
   |-- Is endpoint 'static' or 'login'?
   |   |-- No: Is session['authenticated'] True?
   |   |   |-- No -> Redirect to /login?next=<path>
   |-- Is HTTP method POST?
   |   |-- Yes: Does request.form['csrf_token'] match session['csrf_token']?
   |   |   |-- No -> Abort 400 ("Your form expired or has an invalid security token.")
   |
3. server/routes.py -> Matched Route Handler
   |-- Validates input parameters & formats
   |-- If interacting with storage:
   |   |-- Calls storage.resolve_path() to verify confinement within DATA_ROOT
   |-- If interacting with database:
   |   |-- Calls database.get_db() -> executes parameterized SQL queries
   |
4. Route Handler renders Jinja2 Template (web/templates/*.html)
   |-- Template injects session csrf_token() into mutating forms
   |
5. server/app.py -> add_security_headers()
   |-- Appends CSP, X-Frame-Options, X-Content-Type-Options, etc.
   |-- Appends Cache-Control: no-store for dynamic pages
   |
6. Response returned to Browser
```

---

## 4. Database Schema

The SQLite database file is located at `DATA_ROOT / "batcave.db"`.

```sql
-- Migration 1
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    folder_name TEXT -- Added in Migration 2
);
```

---

## 5. Storage Directory Structure

Personal user data is strictly isolated within `DATA_ROOT`:

```text
DATA_ROOT/
├── batcave.db           # SQLite database file
├── files/               # General file storage (nested folders, uploads)
├── photos/              # Validated photos (JPEG, PNG, GIF, WebP)
├── notes/               # Reserved for file-backed note exports
├── ideas/               # Reserved for file-backed idea exports
├── projects/            # Project storage folders
│   ├── project-1/       # Folder for project ID 1
│   └── project-2/       # Folder for project ID 2
├── backups/             # Backup archives
└── archive/             # Archived files and long-term storage
```

### Safety Principles in Storage
1. **Separation from Code**: `DATA_ROOT` is outside the Git repository. The repository never stores personal files.
2. **Project Folder Isolation**: When project ID $N$ is created, directory `projects/project-N` is provisioned. On project deletion from SQLite, the directory is preserved on disk to guarantee zero data loss.
3. **Legacy Project Handling**: Legacy projects where `folder_name` is `NULL` are handled gracefully without generating unwanted folders on disk.
