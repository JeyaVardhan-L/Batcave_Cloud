# Batcave Cloud — Developer Guide

This guide explains how to set up a development environment, write tests, follow coding patterns, and contribute changes to Batcave Cloud safely.

---

## 1. Development Setup

### 1.1 Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- Git.

### 1.2 Setup Instructions

#### Linux & macOS
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

#### Android (Termux)
```bash
pkg update && pkg install python git libjpeg-turbo
git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
cd Batcave_Cloud

python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

---

## 2. Configuration for Development

Batcave Cloud refuses to boot without a secret key and password hash. Generate a private local configuration outside the repository:

```bash
# Option A: Standard default location (automatically discovered by the server):
python -m server.manage create-config

# Option B: Dedicated development configuration:
python -m server.manage create-config --output ~/.config/batcave-cloud/batcave-dev.env
```

If using a dedicated development configuration, set the environment variables before running:

```bash
# Linux / macOS / Termux
export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave-dev.env
export BATCAVE_DATA_ROOT=~/BatCave_Dev

# Windows PowerShell
$env:BATCAVE_CONFIG_FILE = "$HOME\.config\batcave-cloud\batcave-dev.env"
$env:BATCAVE_DATA_ROOT = "$HOME\BatCave_Dev"
```

Start the development server:

```bash
python -m server.app
```

Navigate to `http://localhost:8080` (or `http://127.0.0.1:8080`).

---

## 3. Automated Test Suite

Batcave Cloud uses `pytest` for automated integration and regression testing.

### 3.1 Running Tests

Always invoke pytest as a module (`python -m pytest`) to ensure the repository root is automatically added to Python's module search path across all platforms:

```bash
python -m pytest -q
```

### 3.2 Test Configuration (`pytest.ini`)
The repository includes a minimal `pytest.ini`:
```ini
[pytest]
addopts = --capture=sys
```
This flag configures system-level standard I/O capture during test runs, preventing output buffering conflicts across diverse operating systems and shell environments.

### 3.3 Test Suite Structure
The test suite consists of 6 modules containing 65 tests:
- `tests/test_foundation.py` (11 tests): Authentication, session cookies, global CSRF enforcement, basic CRUD, root protection, path traversal defenses, upload size limits, Pillow photo validation, and security headers.
- `tests/test_files_v03.py` (8 tests): Breadcrumbs, file metadata, sorting, recursive search, move operations (cycle detection and invalid destinations), storage usage without recursive disk walks, and route CSRF protection.
- `tests/test_notes_v041.py` (7 tests): Note creation, editing/updating (updating `updated_at` without altering `created_at`), deletion, case-insensitive search by title/content, 404 handling, and CSRF protection.
- `tests/test_ideas_v042.py` (11 tests): Idea creation, validation of empty content, edit views, update flow, deletion, content search (ordered newest-first), 404 handling, and CSRF protection.
- `tests/test_projects_v043.py` (14 tests): Project creation (with automatic `project-<id>` folder provisioning), validation, detail/edit views, metadata updates, status changes (`Active`, `Paused`, `Archived`), legacy NULL folder handling, safe folder navigation, path boundary protections, deletion folder retention, and CSRF protection.
- `tests/test_dashboard_v051.py` (14 tests): Dashboard authentication gating, workspace counts, ordering semantics, quick actions, absence of path/secret leakage, automatic config discovery, explicit precedence, and invalid config handling.

### 3.4 Test Isolation Pattern
All tests run in complete isolation using Python's `tempfile.TemporaryDirectory()`. Tests instantiate the Flask application using `create_app({"DATA_ROOT": temp_dir, "SECRET_KEY": "...", "PASSWORD_HASH": "..."})`. No test ever touches real user data or live configuration files.

---

## 4. Coding & Architecture Conventions

When adding or modifying code, adhere strictly to established repository patterns:

1. **Path Safety**:
   - Never use raw string formatting or `os.path.join()` without validation.
   - Always resolve paths against designated root directories using `server.storage.resolve_path()`.
   - Always catch `InvalidPathError` and return appropriate HTTP errors (typically 400).
2. **Database Queries**:
   - Always use parameterized queries (`?` syntax with tuples) via `get_db().execute(...)`.
   - Never concatenate user input into SQL queries.
   - Manage schema additions through versioned migrations in `server/database.py`.
3. **Mutations & CSRF**:
   - All actions that change server state (create, update, delete, upload, rename, move) must use the `POST` method.
   - Forms in Jinja2 templates must include `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
4. **Error Responses**:
   - Use Flask's `abort(404)` or `abort(400, "message")` to leverage central error templates.
   - Do not leak internal exception tracebacks to client responses.
5. **Static Assets & Styling**:
   - Keep styling centralized in `web/static/style.css`.
   - Use responsive layouts with clean typography and consistent color variables.

---

## 5. Development Workflow & Pre-Commit Verification

Follow this workflow for all changes:

```text
1. Branch / Work
   ├── Make focused, incremental modifications
   └── Add corresponding unit tests in tests/
2. Run Test Suite
   └── python -m pytest -q (Ensure all 65 tests pass)
3. Run Syntax Check
   └── python -m compileall server tests
4. Run Git Diff Hygiene Check
   └── git diff --check (Ensure no trailing whitespace or CRLF markers)
5. Review Git Diff
   └── git diff
```

Commands to execute:

```bash
# Step 1: Run tests
python -m pytest -q

# Step 2: Compile Python files
python -m compileall server tests

# Step 3: Check for formatting/whitespace issues
git diff --check
```
