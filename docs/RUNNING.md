# Running Batcave Cloud (Foundation v0.2)

## Requirements

- Python 3.10 or newer
- The packages in `requirements.txt`

For development and tests, install `requirements-dev.txt` instead. From the
repository root:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

On Windows PowerShell, use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## First-time private configuration

Batcave refuses to start without a secret key and password hash. There is no
default password. Generate a private configuration file outside this repository:

```bash
python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
```

The command prompts for a password, generates a random secret key, and writes a
Werkzeug password hash. Keep the resulting file private and never commit it.

The following optional environment variables override the defaults:

| Variable | Default | Purpose |
| --- | --- | --- |
| `BATCAVE_DATA_ROOT` | `/storage/emulated/0/BatCave` | Personal data root |
| `BATCAVE_MAX_UPLOAD_MB` | `25` | Maximum request/upload size |
| `BATCAVE_HOST` | `0.0.0.0` | Flask bind address |
| `BATCAVE_PORT` | `8080` | Flask port |
| `BATCAVE_SECURE_COOKIES` | `false` | Set `true` only behind HTTPS |

`BATCAVE_SECRET_KEY` and `BATCAVE_PASSWORD_HASH` are required, normally through
the private config file above.

Run the isolated test suite with:

```bash
python -m pytest -q
```

## Start locally or on Termux

After exporting `BATCAVE_CONFIG_FILE` and installing dependencies:

```bash
python -m server.app
```

The Android/Termux data default stays at `/storage/emulated/0/BatCave`; the
repository contains code only. For a Windows development run, set
`BATCAVE_DATA_ROOT` to a private directory outside the repository.

## Project structure

- `server/app.py` — application factory, session security, login, errors
- `server/config.py` — environment configuration
- `server/auth.py` — password and CSRF helpers
- `server/storage.py` — safe filesystem and image operations
- `server/database.py` — SQLite connections and additive migrations
- `server/routes.py` — authenticated feature routes
- `tests/` — isolated tests using temporary storage

## Security status and limitations

This is intended for a trusted LAN only. It has no HTTPS, public-internet
deployment, rate limiting, multi-user authorization, malware scanning, or backup
system. Do not port-forward it or expose it to the public internet. Project
directory retention on project deletion is deliberate: it prevents accidental
file loss, but leaves cleanup as a future management feature. Recursive file
counts and photo scans are retained for simplicity and may need indexing as the
collection grows.
