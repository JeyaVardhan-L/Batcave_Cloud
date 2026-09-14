# Changelog

All notable changes to the Batcave Cloud project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to semantic milestone versioning.

---

## [0.4.3] - Projects Workspace Improvements

### Added
- **Project Detail & Edit View**: Added `GET /projects/<id>` and `POST /projects/<id>/update` to inspect and update project names and descriptions.
- **Safe Project Folder Navigation**: Added `GET /projects/<id>/folder` and `GET /projects/<id>/folder/<subpath>` to safely explore files inside the project's dedicated filesystem directory (`projects/project-<id>`).
- **Legacy Project Handling**: Added safe handling for legacy project database records where `folder_name` is `NULL` or missing from disk, displaying an unavailable state without generating stray directories.
- **Project Status Gating**: Hardened `POST /projects/status/<id>` to return friendly 404 responses for nonexistent project IDs and reject invalid status values.
- **Project Tests**: Added `tests/test_projects_v043.py` (14 tests) covering project CRUD, updates, status transitions, folder navigation boundaries, legacy project compatibility, and directory retention.

### Changed
- **Data Retention on Delete**: Project deletion (`POST /projects/delete/<id>`) removes the database record while deliberately preserving the project directory on disk to prevent catastrophic data loss.
- **Database Migration 2**: Applied additive migration `_migration_2` adding the `folder_name TEXT` column to the `projects` table.

---

## [0.4.2] - Ideas Workspace Improvements

### Added
- **Idea Editing**: Added `GET /ideas/<id>` and `POST /ideas/<id>/update` to allow editing captured idea content.
- **Idea Search**: Added case-insensitive search by idea content (`/ideas?q=<query>`), displaying matching results ordered newest-first.
- **Idea Tests**: Added `tests/test_ideas_v042.py` (11 tests) verifying idea capture, validation of empty content, edit views, update flow, newest-first ordering, 404 safety, and CSRF protection.

### Changed
- Preserved `created_at` timestamp on idea updates without introducing an unnecessary `updated_at` column.

---

## [0.4.1] - Notes Workspace Improvements

### Added
- **Note Editing & Updating**: Added `GET /notes/<id>` and `POST /notes/<id>/update` allowing modification of note title and content.
- **Automatic Modification Timestamps**: Added automatic update of `updated_at` to the current timestamp on note edit while strictly preserving original `created_at`.
- **Note Search**: Added case-insensitive search across note title and content (`/notes?q=<query>`), returning results ordered by most recently updated (`ORDER BY updated_at DESC`).
- **Note Tests**: Added `tests/test_notes_v041.py` (7 tests) verifying note creation, edit views, update timestamps, deletion, title/content search, and CSRF protection.

---

## [0.3.0] - Files Workspace Improvements

### Added
- **Clickable Breadcrumb Navigation**: Implemented hierarchical breadcrumbs allowing immediate traversal back to any parent directory.
- **Metadata Inspection**: Added human-readable file sizes, formatted modification timestamps, and distinct file/folder types.
- **Sorting Options**: Implemented sorting by name, file size, or modification date in ascending or descending order.
- **Hierarchy Search**: Added case-insensitive recursive search across the Files hierarchy (`/files?q=<query>`).
- **Safe Move Operations**: Added `POST /files/move` allowing files and folders to be moved to existing target directories with strict cycle detection (preventing moving a folder into itself or any descendant).
- **Filesystem Capacity Metric**: Implemented $O(1)$ storage capacity summary (`shutil.disk_usage`) displaying used, free, and total space without recursive disk walks.
- **Files Tests**: Added `tests/test_files_v03.py` (8 tests) covering breadcrumbs, metadata, sorting, search, move safety, and CSRF protection.

---

## [0.2.0] - Secure Foundation & Modular Architecture

### Added
- **Modular Application Factory**: Refactored monolithic server into separated modules: `server/app.py`, `server/config.py`, `server/auth.py`, `server/database.py`, `server/storage.py`, `server/routes.py`, and `server/manage.py`.
- **Single-User Password Authentication**: Implemented secure session login using `werkzeug.security` password hashing (`check_password_hash`).
- **Global CSRF Protection**: Added cryptographic per-session tokens and automatic validation on all `POST` requests via `@app.before_request`.
- **Path Traversal Defenses**: Implemented `resolve_path()` in `server/storage.py`, enforcing that all filesystem operations remain within authorized roots under `DATA_ROOT`.
- **Security Headers**: Appended `CSP`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Permissions-Policy`, and `Cache-Control: no-store` via `@app.after_request`.
- **Photo Validation**: Added binary image inspection and format matching via Pillow, with decompression bomb limits.
- **Upload Collision Protection**: Enforced atomic, exclusive file creation (`xb`) to prevent overwriting existing files.
- **Configuration Management**: Created CLI `python -m server.manage create-config` to generate random secret keys and password hashes without storing credentials in source control.
- **Automated Test Suite**: Introduced `pytest` test harness with isolated temporary directories in `tests/test_foundation.py` (11 tests).

---

## [0.1.0] - Initial Prototype

### Added
- Early prototype exploring running a self-hosted Flask server on an unused Samsung Galaxy Tab S6 Lite (SM-P615) under Android 13 and Termux.
- Initial dashboard and basic unauthenticated HTML templates for Files, Notes, Ideas, Projects, and Photos.
- Direct SQLite connection for storing basic notes, ideas, and project records.
- Basic file upload and serving directly against `/storage/emulated/0/BatCave`.
