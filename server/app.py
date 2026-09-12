"""Application factory and HTTP-wide security configuration."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

try:  # Supports both `python server/app.py` and `python -m server.app`.
    from .auth import csrf_token, csrf_protect, valid_csrf_token, verify_password
    from .config import build_config, validate_security_config
    from .database import init_app as init_database_app
    from .routes import register_routes
except ImportError:  # pragma: no cover - direct-script deployment path
    from auth import csrf_token, csrf_protect, valid_csrf_token, verify_password
    from config import build_config, validate_security_config
    from database import init_app as init_database_app
    from routes import register_routes


def _safe_next_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or not value.startswith("/"):
        return None
    return value


def create_app(test_config: dict | None = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "web" / "templates"),
        static_folder=str(project_root / "web" / "static"),
    )
    app.config.update(build_config(test_config))
    validate_security_config(app.config)

    data_root = Path(app.config["DATA_ROOT"])
    for folder in ("files", "photos", "notes", "ideas", "projects", "backups", "archive"):
        (data_root / folder).mkdir(parents=True, exist_ok=True)
    init_database_app(app)

    @app.context_processor
    def inject_template_helpers():
        return {"csrf_token": csrf_token}

    @app.before_request
    def require_login_and_csrf():
        allowed_endpoints = {"static", "login"}
        if request.endpoint not in allowed_endpoints and not session.get("authenticated"):
            return redirect(url_for("login", next=request.path))
        if request.method == "POST" and not valid_csrf_token(request.form.get("csrf_token")):
            abort(400, "Your form expired or has an invalid security token.")

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "form-action 'self'; base-uri 'self'; frame-ancestors 'none'",
        )
        if request.endpoint != "static":
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("authenticated"):
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            if verify_password(request.form.get("password", "")):
                session.clear()
                session["authenticated"] = True
                session.permanent = True
                csrf_token()
                return redirect(_safe_next_url(request.form.get("next")) or url_for("dashboard"))
            flash("Invalid password.")
        return render_template("login.html", next_url=_safe_next_url(request.args.get("next")))

    @app.post("/logout")
    @csrf_protect
    def logout():
        session.clear()
        flash("You have been logged out.")
        return redirect(url_for("login"))

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    @app.errorhandler(500)
    def error_page(error):
        messages = {
            400: "The request could not be accepted.",
            403: "You do not have permission to access this resource.",
            404: "The page or file could not be found.",
            413: "The upload is larger than the configured size limit.",
            500: "Something went wrong. Please try again later.",
        }
        return render_template("error.html", error=error, message=messages[error.code]), error.code

    register_routes(app)
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host=application.config["HOST"], port=application.config["PORT"], debug=False)
