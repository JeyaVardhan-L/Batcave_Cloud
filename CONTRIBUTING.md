# Contributing to Batcave Cloud

Batcave Cloud is an educational, self-hosted personal cloud workspace. Contributions, discussions, and improvements are welcome as long as they adhere to the project's engineering principles.

---

## Engineering Principles

1. **Incremental Milestones**: Build small, focused feature slices with clear architectural boundaries. Avoid speculative abstractions, massive rewrites, or unnecessary third-party dependencies.
2. **Security by Default**:
   - Never commit credentials, private keys, environment files, or personal storage data.
   - All forms performing mutations must include CSRF tokens (`csrf_token()`).
   - Every route interacting with user storage must resolve paths strictly within configured root boundaries using `server.storage.resolve_path()`.
   - File uploads must validate names (`clean_name()`), avoid overwriting existing files (`xb` mode), and enforce size limits (`MAX_CONTENT_LENGTH`).
3. **Data Safety**:
   - User data must be protected against accidental loss. Deleting a database record (like a project) deliberately retains its filesystem directory on disk.
4. **Test-Backed Changes**:
   - Every new route, security rule, or storage capability must include corresponding unit and integration tests in the `tests/` directory. Tests must execute in isolated temporary directories without mutating live data.

---

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/JeyaVardhan-L/Batcave_Cloud.git
   cd Batcave_Cloud
   ```

2. **Create a virtual environment & install development dependencies**:
   ```bash
   python -m venv .venv

   # Linux / macOS / Termux
   source .venv/bin/activate
   pip install -r requirements-dev.txt

   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

3. **Generate a local configuration**:
   ```bash
   python -m server.manage create-config
   ```
   *Batcave Cloud automatically discovers the configuration generated at `~/.config/batcave-cloud/batcave.env` on startup. To use a custom path instead, provide `--output <path>` and export `BATCAVE_CONFIG_FILE=<path>`.*

4. **Verify tests pass**:
   ```bash
   python -m pytest -q
   ```
   *(Expected: `65 passed`)*

---

## Pre-Submission Checklist

Before creating a pull request or submitting code, execute the following verification steps:

```bash
# 1. Run the entire test suite (all 65 tests must pass)
python -m pytest -q

# 2. Verify clean Python compilation
python -m compileall server tests

# 3. Check for trailing whitespace, merge conflicts, and formatting issues
git diff --check
```

For complete architectural conventions, database patterns, and test isolation design, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
