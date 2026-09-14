# Contributing to Batcave Cloud

Batcave Cloud is an educational, self-hosted personal cloud workspace. Contributions, discussions, and improvements are welcome as long as they adhere to the project's engineering principles.

## Engineering Principles

1. **Incremental Milestones**: Build small, focused feature slices with clear boundaries. Do not introduce massive rewrites or extraneous dependencies.
2. **Security by Default**:
   - Never commit credentials, private keys, environment files, or personal storage data.
   - All forms performing mutations must include CSRF tokens.
   - Every route interacting with user storage must resolve paths strictly within configured root boundaries using `resolve_path()`.
   - File uploads must validate names (`clean_name()`), avoid overwriting existing files, and enforce size limits.
3. **Data Safety**:
   - User data must be protected against accidental loss. For example, deleting a database record (like a project) deliberately retains its filesystem directory.
4. **Test-Backed Changes**:
   - Every new route, security rule, or storage capability must have corresponding unit/integration tests in the `tests/` directory.

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
   python -m server.manage create-config --output ~/.config/batcave-cloud/batcave.env
   export BATCAVE_CONFIG_FILE=~/.config/batcave-cloud/batcave.env
   ```

4. **Verify tests pass**:
   ```bash
   python -m pytest -q
   ```

## Pre-Submission Checklist

Before creating a commit or pull request, run:

```bash
# 1. Run the entire test suite
python -m pytest -q

# 2. Verify clean Python compilation
python -m compileall server tests

# 3. Check for trailing whitespace and merge conflicts
git diff --check
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for deeper workflow details and architectural patterns.
