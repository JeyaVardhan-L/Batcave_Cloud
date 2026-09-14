# Batcave Cloud — Security Model & Threat Assessment

This document provides a comprehensive breakdown of the security controls implemented in Batcave Cloud (v0.4.3), as well as an explicit enumeration of security limitations.

---

## 1. Threat Model & Intended Operating Environment

Batcave Cloud is designed as a **single-user personal workspace running within a trusted Local Area Network (LAN)** or local loopback environment.

> [!CAUTION]
> **Do not expose Batcave Cloud directly to the public internet via port forwarding.**
> The application is not hardened against public-internet attack vectors. If remote access outside your home network is required, route traffic through a secure, encrypted tunnel such as a private WireGuard / Tailscale VPN or an authenticated HTTPS reverse proxy with rate limiting.

---

## 2. Implemented Security Controls

### 2.1 Authentication & Session Management
- **Single-User Access**: Access to all application views and APIs (except the login screen and static assets) requires an active authenticated session.
- **Password Hashing**: Passwords are never stored in plaintext. They are hashed using `werkzeug.security.generate_password_hash` (PBKDF2/scrypt) during initial configuration.
- **Constant-Time Verification**: Verification uses `werkzeug.security.check_password_hash` to defend against timing attacks.
- **Session Protection**:
  - `SESSION_COOKIE_HTTPONLY = True`: Blocks client-side JavaScript access to session cookies, mitigating cookie theft via cross-site scripting (XSS).
  - `SESSION_COOKIE_SAMESITE = "Lax"`: Provides default CSRF protection for top-level navigation.
  - `SESSION_COOKIE_SECURE`: Configurable via `BATCAVE_SECURE_COOKIES` (enforce `True` when operating behind an HTTPS reverse proxy).
  - Session regeneration on login (`session.clear()`) prevents session fixation attacks.

### 2.2 Cross-Site Request Forgery (CSRF) Defense
- **Cryptographic Tokens**: A 32-byte URL-safe cryptographic token is generated using Python's `secrets` module and stored in the user's session.
- **Global Enforcement**: Every `POST` request to the application is intercepted by the global `@app.before_request` hook. The token submitted in `request.form["csrf_token"]` is compared against the session token using `secrets.compare_digest` (constant-time).
- Requests lacking a valid token are immediately aborted with an HTTP 400 response.

### 2.3 Path Traversal & Filesystem Confinement
- **Storage Sandbox (`resolve_path`)**: All file and directory operations (listing, uploading, downloading, renaming, moving, deleting) resolve targets through `server/storage.py`.
- **Strict Confinement**:
  ```python
  root_resolved = root.resolve()
  candidate = (root / relative_path).resolve()
  candidate.relative_to(root_resolved)
  ```
  Any attempt to escape the designated storage root using relative sequences (`../../`), absolute paths, or symbolic links triggers an `InvalidPathError` and yields an HTTP 400 error.
- **Root Protection**: Operations that modify or delete files pass `allow_root=False`, preventing renaming, moving, or deleting the root storage folders.
- **Cycle & Self-Move Prevention**: Moving a folder into itself or any of its descendant subdirectories is explicitly detected and rejected to prevent filesystem corruption.

### 2.4 Upload Safety & Collision Prevention
- **Name Sanitization (`clean_name`)**: Uploaded filenames are sanitized using Werkzeug's `secure_filename`, stripping path separators (`/`, `\`), null bytes, and shell metacharacters.
- **Atomic, Exclusive Creation**: `save_new_upload()` opens destination files with exclusive binary creation mode (`xb`). If a file with the target name already exists, the upload is rejected with `FileExistsError`, preventing accidental or malicious file overwriting.
- **Partial Stream Cleanup**: If an upload stream fails or is interrupted midway, any partial file created on disk is immediately unlinked.
- **Upload Size Limits**: Uploads are constrained by `MAX_CONTENT_LENGTH` (default: 25 MB). Payloads exceeding the limit are rejected with HTTP 413.

### 2.5 Media & Image Verification
- **Extension & Format Verification**: Photos uploaded to `/photos/upload` must match allowed extensions (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`).
- **Binary Content Inspection**: Files are inspected using Pillow (`Image.open()`, `Image.verify()`). If the internal file format does not match its claimed file extension, the file is rejected.
- **Decompression Bomb Defense**: `Image.MAX_IMAGE_PIXELS` is clamped to `30_000_000` pixels to defend against zip/image bomb attacks intended to exhaust server memory.

### 2.6 HTTP Security Headers
All HTTP responses include hardened security headers injected via `@app.after_request`:
- `X-Content-Type-Options: nosniff` — Prevents MIME-type sniffing by browsers.
- `X-Frame-Options: DENY` — Defends against clickjacking.
- `Referrer-Policy: same-origin` — Protects internal path information from leaking in referrer headers.
- `Permissions-Policy: geolocation=(), microphone=(), camera=()` — Disables browser hardware APIs.
- `Content-Security-Policy`:
  ```text
  default-src 'self'; img-src 'self' data:; style-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'
  ```
  Restricts script and asset execution strictly to local origin.
- `Cache-Control: no-store` — Applied to all dynamic routes to prevent browser history caching of sensitive workspace data on shared client computers.

### 2.7 Database Security
- **SQL Injection Prevention**: All queries across `notes`, `ideas`, and `projects` use parameterized SQLite queries (`?` placeholders). No user input is concatenated into raw SQL strings.
- **Data Retention on Deletion**: When a project is deleted from the database, its filesystem folder is deliberately preserved on disk to prevent accidental data loss.

### 2.8 Open Redirect Protection
- The login endpoint validates the `next` redirect parameter using `_safe_next_url()`. URLs containing a scheme (e.g. `http:`, `https:`) or domain name, or not starting with `/`, are rejected to prevent phishing redirects.

---

## 3. Unmitigated Limitations (Not Implemented)

The following security controls are **NOT** present in Batcave Cloud v0.4.3:

1. **No Built-in TLS / HTTPS**:
   - The native development server runs over cleartext HTTP. On a local Wi-Fi or wired network, unencrypted traffic could be intercepted by untrusted devices on the same subnet.
   - *Mitigation*: If accessed across untrusted networks, place the server behind an HTTPS reverse proxy (e.g., Caddy or Nginx) or use an encrypted VPN tunnel (WireGuard / Tailscale). Set `BATCAVE_SECURE_COOKIES=true`.
2. **No Rate Limiting or Account Lockout**:
   - There is no brute-force defense or exponential backoff on the `/login` endpoint.
   - *Mitigation*: Choose a high-entropy passphrase when running `create-config`.
3. **No Multi-User Access Controls**:
   - The system is single-user. Anyone with the password has full read/write/delete access to all workspaces, files, and records.
4. **No Antivirus / Malware Scanning**:
   - Uploaded files are checked for path safety, size, and image validity, but are not scanned for executable malware or malicious payloads.
5. **No Built-in Encryption at Rest**:
   - SQLite database and storage directories reside unencrypted on the host filesystem.
   - *Mitigation*: Use full-disk encryption (FDE) on the host operating system (e.g., BitLocker, LUKS, or Android device encryption).
6. **No Automated Off-Site Backups**:
   - Backups are currently manual. Hardware failure of the host machine will result in data loss unless external backups are maintained.

---

## 4. Security Incident & Vulnerability Reporting

Because Batcave Cloud is a personal educational project, vulnerabilities should be reported directly via GitHub Issues or discussed in the project repository.
