# Batcave_Cloud

A personal self-hosted cloud and server built from scratch with Python, Flask, SQLite, and filesystem storage, designed to run on devices such as a standard Windows/Linux machine or an Android tablet running Termux.

**Current Release**: `v0.5.1` &nbsp;|&nbsp; **Test Suite**: 65 passed across 6 test modules &nbsp;|&nbsp; **Scope**: Single-user private LAN workspace

---

## Why I Built This

Modern cloud platforms and turnkey container bundles make it easy to deploy services, but they often hide the underlying mechanics of server engineering. Batcave_Cloud was built from the ground up as a hands-on, end-to-end engineering project with several core motivations:

- **Learning Systems & Backend Fundamentals**: Building a complete server from scratch—implementing session-based authentication, cryptographic password hashing, global CSRF defense, filesystem path sandboxing, database schema migrations, and clean HTTP routing without third-party frameworks or heavy ORMs.
- **Understanding Architectural Boundaries**: Learning where responsibilities belong in a growing codebase—separating application factories from route controllers, isolating storage I/O from database queries, and keeping configuration strictly decoupled from source code.
- **Repurposing Available Hardware**: Turning an unused, screen-damaged Samsung Galaxy Tab S6 Lite (SM-P615) running Android 13 into an always-on, low-power personal home server using Termux, an OpenSSH daemon, and home Wi-Fi.
- **Deliberate Construction Over Assembly**: Choosing to build core primitives deliberately rather than stringing together a collection of black-box third-party services whose failure modes are difficult to inspect and reason about.

---

## What It Does

Batcave_Cloud provides a single-user workspace accessible over a local network. All listed capabilities are fully implemented and covered by automated tests:

| Subsystem | Implemented Capabilities |
| :--- | :--- |
| **Authentication** | Password verification via Werkzeug (`scrypt`/PBKDF2), session management, and `next` URL safe redirect validation. |
| **Dashboard** | Command Center at `GET /` aggregating real database counts (Notes, Ideas, Projects), $O(1)$ filesystem capacity summary, quick actions, and recent activity feeds. |
| **Files** | Hierarchical browser with clickable breadcrumbs, file sorting (name, size, date), metadata display, case-insensitive recursive search, atomic uploads (`xb` mode), safe moves with cycle detection, and $O(1)$ disk capacity via `shutil.disk_usage`. |
| **Notes** | Full CRUD workspace with note title/content editing, automatic `updated_at` modification tracking while preserving `created_at`, title/content search, and deletion. |
| **Ideas** | Rapid-capture minimalist inbox, idea text editing, case-insensitive content search, newest-first ordering, and deletion. |
| **Projects** | Project tracking with descriptions and status toggles (`Active`, `Paused`, `Archived`), automatic provisioning of dedicated filesystem directories (`projects/project-<id>`), safe subfolder navigation, legacy `folder_name = NULL` compatibility, and deliberate directory retention on record deletion. |
| **Photos** | Photo gallery grid, safe image serving, and image upload verification with Pillow (verifying image headers against file extensions and enforcing decompression bomb limits). |
| **Persistence** | SQLite database with Write-Ahead Logging (`PRAGMA journal_mode = WAL`), foreign keys, busy timeouts, and additive migrations tracked via `PRAGMA user_version`. |
| **Storage Confinement** | Sandboxed filesystem access confined to a configured `DATA_ROOT` using path canonicalization (`resolve_path`) to prevent path traversal (`../../`). |
| **Security Protections** | Global CSRF token gating on all `POST` requests, strict security headers (CSP, `X-Frame-Options: DENY`, `nosniff`, `Permissions-Policy`), and `Cache-Control: no-store` on authenticated routes. |
| **Deployment & Config** | Platform-neutral automatic discovery of configuration files (`~/.config/batcave-cloud/batcave.env` and `$XDG_CONFIG_HOME`), with explicit override support and zero auto-generated secrets. |

---

## Architecture

Batcave_Cloud follows a clean layered request pipeline:

```text
Browser Client (Local Network)
       │
       ▼
Flask Application Factory (server/app.py)
       │
       ├── Global Request Hook: require_login_and_csrf()
       │   ├── Authentication Check (session["authenticated"])
       │   └── CSRF Gate on POST (secrets.compare_digest)
       │
       ▼
Route Controllers (server/routes.py)
       │
       ├──► SQLite Database (server/database.py)
       │    └── batcave.db (WAL mode, additive migrations)
       │
       └──► Storage Layer (server/storage.py)
            └── Sandboxed Filesystem (DATA_ROOT)
                 ├── files/      notes/     projects/
                 ├── photos/     ideas/     backups/
       │
       ▼
Jinja2 Templates & Static Assets (web/)
       │
       ▼
Response Hook: add_security_headers() (CSP, nosniff, DENY, no-store)
```

### Core Architectural Modules

Every subsystem owns a distinct responsibility with clear boundaries:

- [server/app.py](server/app.py): Application factory (`create_app`), directory bootstrapping, global authentication gate, global CSRF enforcement, security response headers, and central error handlers.
- [server/config.py](server/config.py): Platform-neutral configuration discovery (`find_default_config_path`), environment variable parsing, and startup security validation (`validate_security_config`).
- [server/auth.py](server/auth.py): Password verification (`verify_password`), cryptographic CSRF token generation, and constant-time token comparison (`valid_csrf_token`).
- [server/database.py](server/database.py): SQLite connection management (`get_db`), WAL mode configuration, and additive migrations tracked via `PRAGMA user_version`.
- [server/storage.py](server/storage.py): Path traversal prevention (`resolve_path`), atomic exclusive upload creation (`save_new_upload`), Pillow image verification (`validate_photo`), and $O(1)$ disk capacity calculation (`storage_usage`).
- [server/routes.py](server/routes.py): Authenticated HTTP route handlers for Dashboard, Files, Notes, Ideas, Projects, Photos, and Backups.
- [server/manage.py](server/manage.py): Local CLI management utility (`create-config`) for generating high-entropy secret keys and password hashes.

For an in-depth architectural breakdown, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Repository Structure

```text
Batcave_Cloud/
├── .gitignore               # Excludes secrets (*.env), caches, and user data (BatCave/)
├── batcave.env.example      # Documented configuration template with safe placeholders
├── CONTRIBUTING.md          # Contribution guidelines, coding conventions, and test workflow
├── pytest.ini               # Pytest configuration (--capture=sys)
├── README.md                # Project overview, architecture, and reproduction guide
├── requirements.txt         # Production dependencies (Flask, Pillow)
├── requirements-dev.txt     # Development dependencies (pytest)
├── docs/                    # Deep-dive engineering documentation
│   ├── ARCHITECTURE.md      # Detailed system architecture, component duties, and data flows
│   ├── CHANGELOG.md         # Chronological release and milestone history
│   ├── DEVELOPMENT.md       # Developer guide, test isolation, and coding patterns
│   ├── RUNNING.md           # Operational guide, feature manual, and runtime configuration
│   ├── SECURITY.md          # Security model, threat analysis, and unmitigated limitations
│   └── SETUP.md             # Hardware history and reproduction guide across platforms
├── server/                  # Backend application source code
│   ├── __init__.py
│   ├── app.py               # Application factory, request pipeline, and security middleware
│   ├── auth.py              # Password verification and CSRF token primitives
│   ├── config.py            # Configuration discovery, parsing, and startup validation
│   ├── database.py          # SQLite connection lifecycle and additive migrations
│   ├── manage.py            # Local CLI commands (create-config)
│   ├── routes.py            # Authenticated route controllers for all workspaces
│   └── storage.py           # Path confinement sandbox and upload validation
├── tests/                   # Isolated automated integration and unit test suites
│   ├── test_foundation.py   # v0.2: Auth, CSRF, upload safety, security headers (11 tests)
│   ├── test_files_v03.py    # v0.3: Breadcrumbs, metadata, sorting, search, moves (8 tests)
│   ├── test_notes_v041.py   # v0.4.1: Notes editing, timestamps, search, 404 safety (7 tests)
│   ├── test_ideas_v042.py   # v0.4.2: Ideas capture, editing, search, validation (11 tests)
│   ├── test_projects_v043.py# v0.4.3: Projects editing, folders, retention on delete (14 tests)
│   └── test_dashboard_v051.py# v0.5.1: Dashboard metrics, quick actions, config discovery (14 tests)
└── web/                     # Frontend presentation layer
    ├── static/
    │   └── style.css        # Responsive styling and design system tokens
    └── templates/           # Jinja2 HTML templates inheriting from base.html
        ├── backups.html     # Backups view
        ├── base.html        # Main layout, navigation, and CSRF meta tags
        ├── dashboard.html   # Command Center dashboard view
        ├── error.html       # Friendly error display (400, 403, 404, 413, 500)
        ├── files.html       # Files workspace with breadcrumbs and move modal
        ├── idea_edit.html   # Edit idea form
        ├── ideas.html       # Ideas inbox and search view
        ├── login.html       # Authentication screen
        ├── note_edit.html   # Edit note form
        ├── notes.html       # Notes workspace and search view
        ├── photos.html      # Photo gallery and upload form
        ├── project_detail.html # Project detail and metadata update view
        ├── project_folder.html # Project dedicated folder file browser
        └── projects.html    # Projects list and creation form
```

---

## Engineering Principles

Batcave_Cloud adheres to a set of core engineering rules:

1. **Centralized Security Boundaries**: Authentication gating, CSRF validation, and security headers are enforced globally in `server/app.py` middleware, ensuring individual route handlers cannot inadvertently bypass security checks.
2. **Strict Storage Confinement**: All filesystem interactions are resolved and verified against designated root directories using `resolve_path()` in `server/storage.py`. Arbitrary path manipulation and directory traversal (`../../`) are blocked mathematically.
3. **Configuration-Driven Secrets**: Secrets (`BATCAVE_SECRET_KEY`, `BATCAVE_PASSWORD_HASH`) are loaded from configuration files outside the repository. The application refuses to boot if secrets are missing and never silently generates temporary keys at runtime.
4. **Additive Database Migrations**: Schema updates are managed through versioned migration functions in `server/database.py` tracked by SQLite's `PRAGMA user_version`. Table structures evolve additively without destructive rewrites.
5. **Tested Mutations**: Every state-changing route (create, update, delete, upload, rename, move) has corresponding automated integration tests verifying both positive outcomes and failure modes.
6. **Isolated Test Execution**: Tests run in temporary directories (`tempfile.TemporaryDirectory`) using independent application instances. Tests never modify development databases or personal files.
7. **No Speculative Abstractions**: Components are kept straightforward and auditable. Heavy abstractions (such as generic repository layers or full ORMs) are avoided until concrete architectural requirements demand them.
8. **Performance Over Scan-Heavy Loops**: Common operations (like Dashboard metrics or directory listings) avoid recursive directory walking. Disk capacity is retrieved in $O(1)$ time via `shutil.disk_usage()`.
9. **Understandable Before Clever**: Code is structured to be readable, educational, and maintainable by an individual engineer.

---

## Security

Batcave_Cloud implements defensive security controls appropriate for a private, trusted local network.

### Current Protections (Implemented)

- **Zero Hardcoded Secrets**: Requires explicit configuration of `BATCAVE_SECRET_KEY` and `BATCAVE_PASSWORD_HASH`. See [server/config.py](server/config.py).
- **Constant-Time Password Verification**: Passwords hashed with PBKDF2/scrypt are verified via `werkzeug.security.check_password_hash`. See [server/auth.py](server/auth.py).
- **Global CSRF Enforcement**: All mutating HTTP `POST` requests require a valid cryptographic session token verified via `secrets.compare_digest`. Tested in [tests/test_foundation.py](tests/test_foundation.py).
- **Filesystem Path Confinement**: Path canonicalization via `resolve_path` guarantees that file reads, writes, and deletions stay within `DATA_ROOT`. Traversal attempts trigger HTTP 400 errors.
- **Upload Safety & Collision Defense**: Uploaded filenames are sanitized (`clean_name`), files are written using exclusive binary mode (`xb`) to reject overwrites, and request bodies are capped at `MAX_CONTENT_LENGTH` (default 25 MB).
- **Image Content Verification**: Uploaded images are parsed by Pillow to ensure binary formats match file extensions and to mitigate decompression bombs (`Image.MAX_IMAGE_PIXELS`).
- **Hardened HTTP Headers**: Responses include a strict Content Security Policy (CSP), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Permissions-Policy`, and `Cache-Control: no-store` on authenticated routes.
- **SQL Injection Prevention**: All database interactions use parameterized queries (`?`).

### Scope & Public Internet Boundaries

> [!CAUTION]
> **Batcave_Cloud is currently designed and secured for Local Area Network (LAN) operation only.**
> - The native Python server runs over cleartext HTTP. It must not be exposed directly to the public internet via router port forwarding.
> - Rate limiting, brute-force lockout, and multi-user access controls are not yet implemented.
> - For access outside the home network, traffic must be encapsulated within an encrypted tunnel (e.g., WireGuard or Tailscale) or an authenticated HTTPS reverse proxy.

For complete threat analysis and mitigations, see [docs/SECURITY.md](docs/SECURITY.md).

---

## Reproduce It Yourself

Batcave_Cloud can be deployed and reproduced across multiple operating systems. Complete setup instructions and platform-specific details are documented in [docs/SETUP.md](docs/SETUP.md) and [docs/RUNNING.md](docs/RUNNING.md).

### Quick Start (Linux / macOS / Windows / Android Termux)

```bash
# 1. Clone the repository
git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
cd Batcave_Cloud

# 2. Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate       # On Windows PowerShell: .\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Generate your private configuration (one-time)
python -m server.manage create-config

# 5. Set local data root (on Windows/Linux/macOS; Android defaults automatically)
export BATCAVE_DATA_ROOT=~/BatCave   # On Windows: $env:BATCAVE_DATA_ROOT = "$HOME\BatCave"

# 6. Run the automated test suite
python -m pytest -q

# 7. Start the server
python -m server.app
```

Once running, access the application in your browser at `http://localhost:8080` (or `http://<server-ip>:8080` from another device on the same local Wi-Fi network).

For complete platform guides:
- **Windows**: See [docs/SETUP.md#windows-powershell](docs/SETUP.md#windows-powershell).
- **Linux**: See [docs/SETUP.md#linux-debian-ubuntu-arch-fedora](docs/SETUP.md#linux-debian-ubuntu-arch-fedora).
- **macOS**: See [docs/SETUP.md#macos-apple-silicon--intel](docs/SETUP.md#macos-apple-silicon--intel).
- **Android / Termux**: See [docs/SETUP.md#android-termux](docs/SETUP.md#android-termux) and the original hardware notes.

---

## Documentation Map

Detailed engineering documentation is organized in the `docs/` directory:

| Document | Description |
| :--- | :--- |
| [docs/SETUP.md](docs/SETUP.md) | Step-by-step reproduction instructions across all platforms and historical hardware notes. |
| [docs/RUNNING.md](docs/RUNNING.md) | Operational manual covering daily execution, configuration parameters, and workspace features. |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | In-depth technical architecture, module responsibilities, request lifecycles, and database schemas. |
| [docs/SECURITY.md](docs/SECURITY.md) | Formal threat model, implemented security controls, and explicit operational limitations. |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Developer guide, test suite structure, coding conventions, and pre-commit verification workflows. |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Chronological implementation history from initial prototype to current release. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Engineering principles, repository hygiene standards, and pull request checklist. |

---

## Evolution & Milestones

The project has evolved through disciplined, test-verified milestones reflected in the git commit history:

- **`v0.1` (Initial Prototype)**: Proved execution viability of running a Python/Flask web server on an unused Samsung Galaxy Tab S6 Lite under Android 13 and Termux, directly interfacing with Android shared storage (`/storage/emulated/0/BatCave`). *(Commit `d524d9a`)*
- **`v0.2` (Secure Foundation)**: Refactored the monolithic script into focused modules (`app.py`, `config.py`, `auth.py`, `database.py`, `storage.py`, `routes.py`, `manage.py`). Added password hashing, session login, global CSRF gating, path traversal defense (`resolve_path`), Pillow photo validation, security headers, and an automated test harness. *(Commit `e61201c`)*
- **`v0.3.0` (Files Workspace)**: Built a capable file manager with clickable breadcrumb navigation, metadata inspection, column sorting, recursive search, safe moves with cycle detection, and $O(1)$ disk capacity display. *(Commit `e799969`)*
- **`v0.4.1` (Notes Workspace)**: Upgraded Notes into an editable workspace with title/content editing, automatic `updated_at` modification tracking, title/content search, and robust 404 safety. *(Commit `40803a3`)*
- **`v0.4.2` (Ideas Workspace)**: Enhanced the minimalist Ideas inbox with full editing views, newest-first ordering, content search, and empty-submission validation. *(Commit `7d22cfb`)*
- **`v0.4.3` (Projects Workspace)**: Added project detail views, status workflows (`Active`, `Paused`, `Archived`), safe dedicated folder navigation (`projects/project-<id>`), legacy NULL folder safety, and deliberate filesystem retention upon record deletion. *(Commit `31cb381`)*
- **`v0.5.1` (Command Center Dashboard & Config Discovery)**: Replaced placeholder home view with an authenticated Command Center Dashboard aggregating real database counts, $O(1)$ storage capacity, quick action buttons, and recent feeds. Added platform-neutral automatic configuration discovery (`~/.config/batcave-cloud/batcave.env`), eliminating manual environment exports across shell sessions. *(Commit `578e9d8`)*

---

## Current Limitations

To maintain engineering transparency, the following areas are explicitly **unmitigated or unbuilt** in the current release:

- **LAN-Oriented Only**: The application does not contain native TLS/HTTPS certificate provisioning and is intended strictly for private, trusted local networks.
- **No Direct Public Exposure**: The server must not be exposed to the public internet via port forwarding without an encrypted tunnel or reverse proxy.
- **No Remote Access Layer Yet**: Secure remote access from outside the local network is currently being designed and has not yet been implemented.
- **No Automated Backup / Recovery**: Database snapshots and archive exports are not yet automated. Host hardware failure requires manual restoration from external backups.
- **Single-User Workspace**: There is no multi-user isolation, user registration, role-based access control, or per-user quota management.
- **No Brute-Force Rate Limiting**: The login route does not feature exponential backoff or IP rate limiting.
- **No Antivirus Scanning**: Files are validated for path safety, size limits, and image validity, but are not scanned for malicious payloads.

---

## Roadmap

Batcave_Cloud is developed incrementally as an educational systems engineering project. The planned development sequence includes:

1. **Repository & Documentation Polish**: Consolidate engineering documentation, architecture maps, and contribution standards. *(Current phase)*
2. **Backups & Archive System**: Implement automated database snapshot generation, archive export workflows, and recovery verification tools before exposing the server remotely.
3. **Remote Access Architecture**: Design and implement secure off-LAN access (evaluating encrypted mesh networks like Tailscale/WireGuard vs. cloud tunnel relays) with strict security boundaries and encrypted transport.
4. **Production Hardening & Deployment**: Containerization options, process supervision, reverse proxy configurations, and TLS automation.
5. **Feature & UI Expansion**: Additional media viewing enhancements, search optimizations, and workspace utilities.

---

*Batcave_Cloud is built deliberately as an open engineering project to explore backend systems, storage security, and self-hosted infrastructure.*
