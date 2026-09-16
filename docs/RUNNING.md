# Running Batcave Cloud (v0.5.1)

This document is the operational guide for configuring, starting, and using Batcave Cloud in daily operations.

---

## 1. Quick Start

### 1.1 Requirements
- Python 3.10 or newer.
- Dependencies from `requirements.txt` (or `requirements-dev.txt` for development/testing).

### 1.2 Installation
From the repository root:

```bash
# Linux / macOS / Termux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 2. Configuration

Batcave Cloud strictly separates configuration from code. The application will refuse to start unless both `BATCAVE_SECRET_KEY` and `BATCAVE_PASSWORD_HASH` are provided.

### 2.1 First-Time Configuration Generator
Generate a private configuration file outside the repository using the built-in CLI:

```bash
# Any platform (defaults to ~/.config/batcave-cloud/batcave.env):
python -m server.manage create-config

# Or specify a custom output path explicitly:
python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
```

The CLI will prompt you to enter and confirm your password. It will then generate a 48-byte cryptographically secure session key and a Werkzeug password hash, writing them to the default configuration path (`~/.config/batcave-cloud/batcave.env`) with restricted file permissions (`0600` on POSIX systems).

### 2.2 Automatic Discovery vs. Explicit Configuration

In **v0.5.1**, Batcave Cloud automatically discovers the default configuration file:

1. **Automatic Discovery (Default)**: If `BATCAVE_CONFIG_FILE` is not set in your shell environment, Batcave Cloud looks for configuration in standard user paths:
   - `$XDG_CONFIG_HOME/batcave-cloud/batcave.env` (if `XDG_CONFIG_HOME` is set)
   - `~/.config/batcave-cloud/batcave.env` (platform-neutral user home)

   Once you have generated your configuration file at the default path with `create-config`, you do **not** need to manually `export BATCAVE_CONFIG_FILE` each time a new terminal or Termux session is opened.

2. **Explicit `BATCAVE_CONFIG_FILE` Override**: Setting `BATCAVE_CONFIG_FILE` explicitly continues to take absolute precedence:
   ```bash
   export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/custom.env
   ```
   If an explicit file path is given and the file does not exist, the server will raise an immediate error instead of silently falling back.

The application supports the following environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `BATCAVE_CONFIG_FILE` | *(Auto-discovered)* | Explicit path to a private `KEY=value` config file (overrides default discovery) |
| `BATCAVE_SECRET_KEY` | *(None, Required)* | Secret key for cryptographic session signing |
| `BATCAVE_PASSWORD_HASH` | *(None, Required)* | Werkzeug password hash for single-user authentication |
| `BATCAVE_DATA_ROOT` | `/storage/emulated/0/BatCave` | Filesystem path where user data, uploads, and SQLite database are stored |
| `BATCAVE_MAX_UPLOAD_MB` | `25` | Maximum allowed upload and request size in megabytes |
| `BATCAVE_HOST` | `0.0.0.0` | IP address for the Flask server to bind to |
| `BATCAVE_PORT` | `8080` | Port number for the HTTP server |
| `BATCAVE_SECURE_COOKIES` | `false` | When set to `true`, session cookies require HTTPS transport |

> [!IMPORTANT]
> When running on **Windows, Linux, or macOS**, override `BATCAVE_DATA_ROOT` to a local folder (e.g. `~/BatCave` or `C:\Users\<Name>\BatCave`), as the default path is specific to Android shared storage.

---

## 3. Starting the Server

Once your configuration file is generated (or environment variables are set), start the server:

```bash
python -m server.app
```

Output:
```text
 * Serving Flask app 'server.app'
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://<local-ip>:8080
```

Open your web browser and visit `http://localhost:8080` (or the LAN IP of the host machine). Log in with the password configured during setup.

---

## 4. Workspace Features

### 4.1 Dashboard / Command Center (`/`)
The Dashboard is the primary home page for Batcave Cloud:
- **Storage Summary**: Displays total, used, and free capacity of the storage volume hosting `DATA_ROOT` using $O(1)$ disk metrics without traversing directory trees.
- **Workspace Statistics**: Real-time counts for Notes, Ideas, and Projects (including active status counts) alongside storage metrics.
- **Quick Actions**: One-click action buttons to quickly start a new Note, capture an Idea, start a Project, or open the Files manager without navigating separate menus.
- **Recent Notes**: Displays the 5 most recently updated notes (`updated_at DESC, id DESC`) linking directly to their editing views.
- **Recent Ideas**: Displays the 5 newest ideas (`created_at DESC, id DESC`) linking directly to their editing views.
- **Active Projects**: Lists current active projects (`status = 'Active'`) linking to their detail views.

### 4.2 Files Workspace (`/files`)
- **Navigation**: Click folders to navigate subdirectories; click breadcrumbs in the header to return immediately to parent directories.
- **Sorting**: Click column headers to sort files and folders by **Name**, **Size**, or **Modified Date** in ascending or descending order.
- **Search**: Enter a search query in the search bar (`?q=...`) to perform a case-insensitive recursive search across the Files hierarchy. Search is the only Files action that recursively traverses subfolders.
- **Upload & New Folder**: Upload files up to `BATCAVE_MAX_UPLOAD_MB` (default 25 MB). Existing files are protected and will not be overwritten on duplicate upload.
- **Move**: Move a file or folder into any existing directory by providing its target path (e.g., `archive/2026`). Cycle detection prevents moving a folder into itself or any of its descendants.
- **Storage Summary**: The footer displays the total, used, and free capacity of the filesystem hosting `DATA_ROOT` via `shutil.disk_usage()`.

### 4.3 Notes Workspace (`/notes`)
- **Capture**: Add notes with a title and content.
- **Edit**: Click on any note to open the edit page (`/notes/<id>`). Updating a note updates its `updated_at` timestamp while preserving its original `created_at`.
- **Search**: Search notes by title or content. Results are returned ordered by most recently updated (`ORDER BY updated_at DESC`).
- **Delete**: Permanently remove a note from the SQLite database.

### 4.4 Ideas Workspace (`/ideas`)
- **Quick-Capture Inbox**: Capture thoughts and quick ideas with single-field submission.
- **Edit**: Click on an idea to open its edit page (`/ideas/<id>`). Editing preserves original creation timestamp (`created_at`).
- **Search**: Search ideas by content. Results are returned ordered newest-first.
- **Delete**: Remove an idea when processed.

### 4.5 Projects Workspace (`/projects`)
- **Project Provisioning**: Creating a project automatically provisions an isolated directory under `DATA_ROOT / "projects" / project-<id>`.
- **Detail & Edit**: Open `/projects/<id>` to view and update project name, description, and status.
- **Status Management**: Toggle between `Active`, `Paused`, and `Archived`.
- **Folder Navigation**: Click **Open Project Folder** (`/projects/<id>/folder`) to browse files located inside the project's dedicated directory. Path traversal protections ensure browsing cannot escape the project folder.
- **Legacy Project Compatibility**: Projects created prior to v0.4.3 without an assigned folder (`folder_name = NULL`) display an unavailable indicator without crashing or generating unintended directories.
- **Data Retention on Delete**: Deleting a project removes the database record while **deliberately keeping the project directory on disk** to prevent catastrophic data loss.

### 4.6 Photos Workspace (`/photos`)
- **Grid View**: Displays all photos found inside `DATA_ROOT / "photos"`.
- **Upload Validation**: Photo uploads are validated using Pillow. Formats are verified against file extensions, and decompression bomb protection is enforced.
- **Safe Serving**: Photos are served securely from the photos directory with content-type verification.

---

## 5. Security & Operating Limitations

- **LAN Only**: Batcave Cloud does not implement native TLS/HTTPS. It is intended for use inside your private, password-protected Wi-Fi or wired home network.
- **No Port Forwarding**: Never expose the HTTP port directly to the internet.
- **Remote Access Recommendation**: For access away from home, use an encrypted VPN tunnel (such as WireGuard, Tailscale, or OpenVPN) or an authenticated reverse proxy with HTTPS (such as Caddy or Nginx) and set `BATCAVE_SECURE_COOKIES=true`.
