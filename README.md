# Batcave Cloud

A self-hosted, single-user personal cloud workspace designed for Local Area Networks (LAN). Built with Python, Flask, SQLite, and vanilla web technologies, Batcave Cloud was originally created to turn an unused Android tablet into an always-on home server, and has evolved into an educational, modular personal cloud system.

**Current Version**: `v0.4.3`
<br>
**Test Suite**: 51 passed (automated integration and unit tests)

---

## Why Batcave Cloud?

Modern cloud storage platforms often obscure how networking, storage abstraction, authentication, and database migrations function under the hood. Batcave Cloud was created as a hands-on, end-to-end engineering learning project with two core motivations:

1. **Practical Systems Engineering**: Gain direct experience building and maintaining a real Linux-based server environment—covering user isolation, filesystem sandboxing, session security, database schema evolution, and network administration.
2. **Repurposing Surplus Hardware**: Transform an unused, screen-damaged Samsung Galaxy Tab S6 Lite (SM-P615) running Android 13 into a functional, low-power, always-on personal home server using Termux and OpenSSH.

Rather than deploying a pre-packaged, black-box container or an off-the-shelf software suite, Batcave Cloud is written from scratch in Python to explore how web security primitives and storage architectures operate at a fundamental level.

---

## What It Can Do

Batcave Cloud currently provides a secure, web-based workspace with the following capabilities:

### Authentication & Security
- **Single-User Password Authentication**: Access is protected by a session-based login screen using industry-standard password hashing via Werkzeug (`scrypt`/PBKDF2).
- **Global CSRF Protection**: Every mutating HTTP `POST` request is validated against a per-session cryptographic token using constant-time comparison.
- **Strict Storage Confinement**: All filesystem interactions are sandboxed within a configured data root using path canonicalization (`resolve_path`) to prevent path traversal (`../../`).
- **Upload Safety**: Filenames are sanitized via Werkzeug's `clean_name`, duplicate uploads are rejected to prevent accidental overwrites (`O_EXCL` / `xb` mode), and request sizes are bounded by a 25 MB default limit.
- **Photo Content Validation**: Image uploads are inspected with Pillow to verify that internal image formats match their file extensions, and decompression bomb protection is enforced.
- **Hardened HTTP Headers**: Responses include Content Security Policy (CSP), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Permissions-Policy`, and `Cache-Control: no-store` on authenticated routes.

### Files Workspace
- **Breadcrumb Navigation**: Seamless traversal across nested directory hierarchies.
- **Metadata & Sorting**: Displays human-readable file sizes, modification timestamps, and distinct file types. Items can be sorted by name, size, or date (ascending and descending).
- **Hierarchy Search**: Case-insensitive recursive search across all files and subdirectories.
- **Safe Directory Operations**: Create folders, rename items, and delete empty folders or files.
- **Safe Moves**: Move files and folders into existing target folders with cycle detection (preventing moving a directory into itself or its descendants).
- **Filesystem Capacity**: Real-time disk capacity summary (used, free, total) via `shutil.disk_usage()` without slow recursive file walks.

### Notes Workspace
- **CRUD Operations**: Create, view, edit, update, and delete notes.
- **Preserved History**: Editing notes updates an `updated_at` timestamp while preserving the original creation date (`created_at`).
- **Search**: Search notes by title or content, ordered by most recently updated.

### Ideas Workspace
- **Quick-Capture Inbox**: Minimalist, single-field capture for rapid thought collection.
- **Editing**: View and modify captured ideas while preserving initial capture timestamps.
- **Search**: Case-insensitive text search across ideas, ordered newest-first.

### Projects Workspace
- **Project Tracking**: Manage projects with names, descriptions, and statuses (`Active`, `Paused`, `Archived`).
- **Dedicated Folders**: Automatically provisions a dedicated directory on disk (`projects/project-<id>`) upon creation.
- **Folder Navigation**: Safely explore and view files inside a project's folder without escaping its directory boundaries.
- **Legacy Project Support**: Gracefully displays legacy projects that lack an associated folder (`folder_name = NULL`) without crashing or creating unintended directories.
- **Data Retention on Deletion**: Deleting a project removes the database record while **deliberately retaining the directory on disk** to avoid catastrophic data loss.

### Storage & Database
- **SQLite Database**: Uses Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and versioned additive migrations for robust concurrency and schema tracking.
- **Clean Storage Layout**: Seven organized root folders (`files`, `photos`, `notes`, `ideas`, `projects`, `backups`, `archive`) isolated from the application code.

---

## Project Evolution

The project developed through disciplined, test-driven iterations:

```text
v0.1 (Prototype)
  └── Monolithic Flask script on Android/Termux, unauthenticated HTML/CSS UI
v0.2 (Secure Foundation)
  └── Modular refactor, password hashing, session login, global CSRF, storage sandbox, test suite
v0.3 (Files Workspace)
  └── Breadcrumbs, metadata, sorting, recursive search, safe moves, disk quota
v0.4.1 (Notes Workspace)
  └── Note editing, updated_at timestamps, title/content search, 404 safety
v0.4.2 (Ideas Workspace)
  └── Quick-capture inbox, idea editing, newest-first search
v0.4.3 (Projects Workspace) [Current]
  └── Project detail/edit, status gating, folder navigation, NULL folder safety, folder retention on delete
```

### v0.1 — Initial Prototype
- **What Changed**: Set up an initial proof-of-concept on a Samsung Galaxy Tab S6 Lite running Android 13 and Termux. Created a monolithic `server/app.py` serving early HTML templates for Files, Notes, Ideas, Projects, and Photos.
- **Why**: Proved that an unused tablet could run a persistent Python web server over home Wi-Fi and interface with Android shared storage (`/storage/emulated/0/BatCave`).
- **Engineering Reality**: The prototype proved viable hardware execution, but lacked authentication, CSRF defense, path traversal protection, automated tests, or modular structure.

### v0.2 — Secure Foundation
- **What Changed**: Complete architectural rewrite. Split the monolithic app into focused modules (`app.py`, `config.py`, `auth.py`, `database.py`, `storage.py`, `routes.py`, `manage.py`). Added Werkzeug password hashing, session-based authentication, global CSRF gating on all POST requests, path confinement (`resolve_path`), photo validation via Pillow, security headers, and an automated test suite (`tests/test_foundation.py`).
- **Why**: Established a secure baseline before adding advanced features. Personal data must never be exposed without authentication and input validation.
- **Verification**: 11 automated tests introduced and passing in temporary test directories.

### v0.3 — Files Workspace
- **What Changed**: Transformed raw file listing into a capable file manager. Added clickable breadcrumbs, file metadata (formatted size, timestamp), sorting (name, size, date), recursive search (`?q=...`), safe move operations with cycle/descendant detection, and an $O(1)$ filesystem capacity summary.
- **Why**: Provided everyday utility for managing personal files while ensuring operations could not escape storage bounds or corrupt directory hierarchies.
- **Verification**: 8 new automated tests (`tests/test_files_v03.py`).

### v0.4.1 — Notes Workspace
- **What Changed**: Upgraded Notes from a write-only list into an editable workspace. Added `GET /notes/<id>` and `POST /notes/<id>/update`, automatic `updated_at` timestamps, case-insensitive title/content search, and robust 404 error handling.
- **Why**: Notes require revision and searchability to be useful for daily capture and recall.
- **Verification**: 7 new automated tests (`tests/test_notes_v041.py`).

### v0.4.2 — Ideas Workspace
- **What Changed**: Enhanced the Ideas inbox with editing (`GET /ideas/<id>`, `POST /ideas/<id>/update`) and search capabilities (`/ideas?q=...`), while intentionally preserving its minimalist, newest-first capture design.
- **Why**: Quick thoughts require rapid retrieval and editing without the formal structure of a full note.
- **Verification**: 11 new automated tests (`tests/test_ideas_v042.py`).

### v0.4.3 — Projects Workspace (Current)
- **What Changed**: Built project detail and editing views (`GET /projects/<id>`, `POST /projects/<id>/update`), status transitions (`Active`, `Paused`, `Archived`), and safe project folder navigation (`/projects/<id>/folder`). Handled legacy NULL folders gracefully, and enforced filesystem folder retention upon project record deletion.
- **Why**: Bridged database project metadata with dedicated filesystem folders, ensuring that deleting a project metadata entry never deletes project source files.
- **Verification**: 14 new automated tests (`tests/test_projects_v043.py`).

---

## Current Status

- **Release**: `v0.4.3`
- **Automated Tests**: 51 passing tests across 5 test suites.
- **Verified Compatibility**: Windows 11 / PowerShell, Linux (Ubuntu/Debian), macOS, and Android 13 (Termux `aarch64`).
- **Codebase Health**: Zero external runtime dependencies beyond Flask and Pillow; fully typed server modules with clean test isolation.

---

## Architecture

Batcave Cloud strictly separates responsibilities into modular backend services:

```text
Browser Client (LAN)
       │
       ▼
Flask WSGI Pipeline (server/app.py)
  ├── @app.before_request (Auth Gate & CSRF Verification)
  ├── Route Dispatcher (server/routes.py)
  └── @app.after_request (Security Headers & Cache-Control)
       │
       ├───────────────────────────────┐
       ▼                               ▼
Storage Layer (server/storage.py)   Database Layer (server/database.py)
  ├── Path Confinement (resolve_path) ├── SQLite (WAL Mode, foreign_keys)
  ├── Upload Safety & Excl Creation   └── Additive Migrations (PRAGMA user_version)
  └── Pillow Media Validation          │
       │                               ▼
       ▼                        batcave.db
Batcave Data Directory (DATA_ROOT)
  ├── files/    photos/   notes/
  └── ideas/    projects/ backups/
```

### Module Responsibilities

| Module | Primary Responsibility |
| :--- | :--- |
| `server/app.py` | Application factory (`create_app`), global before/after request middleware, login/logout, and central error handlers. |
| `server/config.py` | Environment variable parsing, private config file loading, and security validation. |
| `server/auth.py` | Password verification (`check_password_hash`), cryptographic CSRF token generation and validation. |
| `server/database.py` | SQLite connection pooling, WAL mode initialization, and additive schema migrations. |
| `server/storage.py` | Path traversal prevention (`resolve_path`), exclusive atomic uploads, and Pillow image verification. |
| `server/routes.py` | Authenticated controller endpoints for Files, Notes, Ideas, Projects, Photos, and Backups. |
| `server/manage.py` | Local administration CLI (`create-config`) for generating secret keys and password hashes. |
| `web/templates/` | Jinja2 HTML templates inheriting from `base.html`. |
| `web/static/` | Shared styling (`style.css`) with responsive design and theme variables. |

For an in-depth architectural breakdown, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Repository Structure

```text
Batcave_Cloud/
├── .gitignore               # Excludes secrets, caches, personal BatCave data
├── batcave.env.example      # Safe configuration template with placeholders
├── CONTRIBUTING.md          # Guidelines for contributing and testing
├── pytest.ini               # Pytest configuration (--capture=sys)
├── README.md                # Project landing page and documentation
├── requirements.txt         # Production runtime dependencies (Flask, Pillow)
├── requirements-dev.txt     # Development & testing dependencies (pytest)
├── docs/                    # Deep-dive documentation
│   ├── ARCHITECTURE.md      # Detailed system architecture and data flows
│   ├── CHANGELOG.md         # Chronological project changelog (v0.1 to v0.4.3)
│   ├── DEVELOPMENT.md       # Developer guide, conventions, and test patterns
│   ├── RUNNING.md           # Operational guide and feature manual
│   └── SETUP.md             # Complete reproduction guide & hardware history
├── server/                  # Backend application code
│   ├── __init__.py
│   ├── app.py               # Application factory & HTTP security pipeline
│   ├── auth.py              # Password verification & CSRF protection
│   ├── config.py            # Environment configuration & validation
│   ├── database.py          # SQLite connection and migrations
│   ├── manage.py            # CLI management commands (create-config)
│   ├── routes.py            # Authenticated route controllers
│   └── storage.py           # Storage sandbox and image verification
├── tests/                   # Isolated automated test suites
│   ├── test_foundation.py   # v0.2: Auth, CSRF, upload safety, headers (11 tests)
│   ├── test_files_v03.py    # v0.3: Breadcrumbs, metadata, sort, search, move (8 tests)
│   ├── test_notes_v041.py   # v0.4.1: Notes editing, timestamps, search (7 tests)
│   ├── test_ideas_v042.py   # v0.4.2: Ideas capture, editing, search (11 tests)
│   └── test_projects_v043.py# v0.4.3: Projects editing, folders, retention (14 tests)
└── web/                     # Frontend presentation layer
    ├── static/
    │   └── style.css        # Responsive styling and design system
    └── templates/           # Jinja2 templates (login, dashboard, files, etc.)
```

---

## Security Model

Security is grounded in defensive programming principles tailored for a private LAN environment:

### Implemented Protections
- **Zero Default Passwords**: The server refuses to boot unless `BATCAVE_SECRET_KEY` and `BATCAVE_PASSWORD_HASH` are defined.
- **Cryptographic Hashing**: Passwords are hashed using Werkzeug (`scrypt`/PBKDF2) and evaluated with constant-time comparison.
- **Global CSRF Enforcement**: All mutating requests (`POST`) require a valid session CSRF token.
- **Filesystem Confinement**: All file routes resolve target paths using `Path.resolve()` and verify that the target starts within the root path using `Path.relative_to()`. Path traversal attempts (`../../`) trigger HTTP 400 errors.
- **No Overwrite on Upload**: Uploads use Python's exclusive creation mode (`xb`) to reject collisions.
- **Pillow Media Verification**: Uploaded photos are inspected for decompression bombs and format mismatches.
- **Safe Database Access**: All SQLite interactions use parameterized queries (`?`).
- **Data Preservation**: Deleting a project removes the database row but intentionally keeps the filesystem directory intact.

### Unmitigated Limitations (Not Implemented)
- **No Native HTTPS**: Traffic over LAN is unencrypted HTTP. Do not run on untrusted public Wi-Fi without a VPN or reverse proxy.
- **No Rate Limiting**: The login endpoint does not feature brute-force rate limiting.
- **Single User**: No multi-user permissions, roles, or quotas.
- **No Antivirus Scanning**: Files are not scanned for malicious executable code.

For complete details and threat mitigations, see [docs/SECURITY.md](docs/SECURITY.md).

---

## Data & Storage Model

Batcave Cloud maintains a strict separation between code and user data. Personal files are never stored inside the Git repository.

```text
DATA_ROOT/ (Configured via BATCAVE_DATA_ROOT)
├── batcave.db               # SQLite database file (WAL mode enabled)
├── files/                   # General file repository (nested folders supported)
├── photos/                  # Validated image files
├── notes/                   # Reserved for note file exports
├── ideas/                   # Reserved for idea file exports
├── projects/                # Dedicated project directories
│   ├── project-1/           # Folder for project ID 1
│   └── project-2/           # Folder for project ID 2
├── backups/                 # Backup archives
└── archive/                 # Long-term archive directory
```

### Schema & Migrations
Database tables are managed with versioned migrations in `server/database.py`:
- **Migration 1**: Creates `notes` (with `updated_at`), `ideas`, and `projects`.
- **Migration 2**: Adds `folder_name TEXT` to `projects`.
- SQLite version tracking is handled via `PRAGMA user_version`.

### Project Folder Lifecycles
When a project is created, a dedicated folder `projects/project-<id>` is provisioned. If a user deletes the project record from the database, the folder is **retained on disk** to prevent data loss. Legacy projects with `folder_name = NULL` are displayed safely without generating unwanted directories.

---

## Setup From Scratch

### 1. Prerequisites
- Python 3.10+ (tested up to 3.14)
- Git

### 2. Clone and Setup Environment

#### Linux / macOS
```bash
git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
cd Batcave_Cloud

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

#### Windows (PowerShell)
```powershell
git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
cd Batcave_Cloud

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

### 3. Generate Private Configuration
Create your secret key and password hash outside the repository:

```bash
# Linux / macOS / Termux
python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
export BATCAVE_DATA_ROOT=~/BatCave

# Windows PowerShell
python -m server.manage create-config --output "$HOME\.config\batcave-cloud\batcave.env"
$env:BATCAVE_CONFIG_FILE = "$HOME\.config\batcave-cloud\batcave.env"
$env:BATCAVE_DATA_ROOT = "$HOME\BatCave"
```

### 4. Run the Tests
```bash
python -m pytest -q
```
*(Expected: `51 passed`)*

### 5. Start the Server
```bash
python -m server.app
```
Open your browser at `http://localhost:8080` (or `http://<lan-ip>:8080`) and log in.

---

## Platform Guides

### Windows (PowerShell)
Windows is fully supported for development and local serving:
```powershell
git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
cd Batcave_Cloud
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m server.manage create-config --output "$HOME\.config\batcave-cloud\batcave.env"
$env:BATCAVE_CONFIG_FILE = "$HOME\.config\batcave-cloud\batcave.env"
$env:BATCAVE_DATA_ROOT = "$HOME\BatCave"
python -m server.app
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update && sudo apt install -y python3 python3-venv git
git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
cd Batcave_Cloud
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
export BATCAVE_DATA_ROOT=~/BatCave
python -m server.app
```

### macOS
```bash
git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
cd Batcave_Cloud
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
export BATCAVE_DATA_ROOT=~/BatCave
python -m server.app
```

### Android (Termux)
The original deployment target for Batcave Cloud:
1. Install **Termux from F-Droid**.
2. Install prerequisites:
   ```bash
   pkg update && pkg install -y python git openssh libjpeg-turbo
   termux-setup-storage
   ```
3. Clone and install:
   ```bash
   git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git ~/Batcave_Cloud
   cd ~/Batcave_Cloud
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
4. Generate config and run with wake-lock:
   ```bash
   python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
   export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
   termux-wake-lock
   python -m server.app
   ```
*(On Android, `BATCAVE_DATA_ROOT` automatically defaults to `/storage/emulated/0/BatCave` in shared storage).*

For complete platform notes and hardware history, see [docs/SETUP.md](docs/SETUP.md).

---

## Configuration

Configuration values are parsed from environment variables or loaded from the file referenced by `BATCAVE_CONFIG_FILE`.

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `BATCAVE_CONFIG_FILE` | *(None)* | Path to private `KEY=value` configuration file |
| `BATCAVE_SECRET_KEY` | *(Required)* | High-entropy string for session signing |
| `BATCAVE_PASSWORD_HASH` | *(Required)* | Werkzeug password hash string |
| `BATCAVE_DATA_ROOT` | `/storage/emulated/0/BatCave` | Path to storage directory holding personal files & database |
| `BATCAVE_MAX_UPLOAD_MB` | `25` | Maximum allowed upload size in megabytes |
| `BATCAVE_HOST` | `0.0.0.0` | Bind IP address for Flask |
| `BATCAVE_PORT` | `8080` | Port for Flask web server |
| `BATCAVE_SECURE_COOKIES`| `false` | Enforce HTTPS-only session cookies |

See [batcave.env.example](batcave.env.example) for a safe configuration template.

---

## Running the Tests

The test suite runs with complete filesystem isolation using temporary directories:

```bash
python -m pytest -q
```

Output:
```text
...................................................                      [100%]
51 passed in 37.93s
```

Test coverage by module:
- `tests/test_foundation.py` (11 tests): Auth, session cookies, CSRF gating, traversal defense, uploads.
- `tests/test_files_v03.py` (8 tests): Breadcrumbs, sorting, hierarchy search, moves, disk quota.
- `tests/test_notes_v041.py` (7 tests): Notes CRUD, editing, `updated_at` timestamps, search.
- `tests/test_ideas_v042.py` (11 tests): Ideas capture, editing, newest-first search, validation.
- `tests/test_projects_v043.py` (14 tests): Projects detail/editing, folder navigation, NULL folder safety, folder retention on delete.

---

## Development Workflow

1. **Clone repository & activate virtual environment**.
2. **Configure development environment** with `BATCAVE_DATA_ROOT` pointing to a scratch folder.
3. **Make focused, incremental modifications** in small feature slices.
4. **Add or update unit tests** in `tests/`.
5. **Run tests**: `python -m pytest -q`.
6. **Compile code**: `python -m compileall server tests`.
7. **Check formatting & whitespace**: `git diff --check`.
8. **Review changes**: `git diff`.
9. **Commit**: Keep commit messages concise and descriptive.

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed guidelines.

---

## Design Decisions

- **SQLite instead of PostgreSQL/MySQL**: For a single-user personal cloud running on low-power devices, SQLite with WAL mode delivers high performance, zero external service maintenance, and atomic database backups in a single file.
- **Additive Migrations**: Schema updates are managed via SQLite's `PRAGMA user_version` through small, ordered migration functions rather than heavy ORM migration frameworks.
- **Decoupled Architecture**: Separating `app.py`, `config.py`, `auth.py`, `database.py`, `storage.py`, and `routes.py` makes security properties auditable and unit-testable.
- **Path Resolution Confinement**: Using `Path.resolve()` combined with `Path.relative_to()` creates a strict mathematical sandbox against directory traversal attacks.
- **Folder Retention on Project Deletion**: When a project is removed from the database, its filesystem folder is deliberately preserved to prevent accidental deletion of user work.
- **Explicit Search vs. Recursive Scanning**: Directory listings never walk subtrees recursively. Only explicit user searches trigger recursive scans.
- **Graceful Legacy Handling**: Missing directories or NULL database values for legacy projects are handled gracefully with informative UI indicators rather than auto-generating directories.

---

## Known Limitations

- **LAN-Oriented Only**: Batcave Cloud has no native TLS or certificate automation. It is intended for private home Wi-Fi networks. Do not port-forward port 8080 to the public internet.
- **Single-User Workspace**: There are no multiple accounts, role-based access control, or per-user permission boundaries.
- **No Brute-Force Rate Limiting**: The login route does not implement exponential backoff or IP rate limiting.
- **No Antivirus Scanning**: Uploaded files are verified for path safety and image validity, but not scanned for malware.
- **No Automated Cloud Backups**: The system relies on local backups. Host machine failure requires manual restoration.

---

## Roadmap

### Completed Milestones
- [x] **v0.1**: Initial hardware exploration and prototype on Android / Termux.
- [x] **v0.2**: Secure foundation refactoring, authentication, CSRF, storage sandbox, security headers, automated test harness.
- [x] **v0.3**: Files workspace with breadcrumbs, sorting, metadata, hierarchy search, moves, and storage capacity display.
- [x] **v0.4.1**: Notes workspace with editing, update timestamps, and search.
- [x] **v0.4.2**: Ideas workspace with quick-capture, editing, and newest-first search.
- [x] **v0.4.3**: Projects workspace with detail/edit views, folder exploration, safe NULL folder handling, and directory retention.

### Next / Planned Explorations
- **Photos Enhancements**: Album categorization, lightweight thumbnail generation, and date-taken metadata extraction.
- **Backup Automation**: Scheduled local archive generation of database and user storage.
- **Encrypted Remote Access Guide**: Documenting step-by-step Tailscale / WireGuard setup for accessing Batcave Cloud securely outside the home network.
- **Storage Indexing**: Background indexing for large photo and file collections to replace runtime `rglob` scans.
