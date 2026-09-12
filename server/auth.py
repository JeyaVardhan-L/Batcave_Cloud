"""Single-user authentication and CSRF helpers."""

from __future__ import annotations

import secrets
from functools import wraps

from flask import abort, current_app, redirect, request, session, url_for
from werkzeug.security import check_password_hash


def csrf_token() -> str:
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def valid_csrf_token(token: str | None) -> bool:
    expected = session.get("csrf_token")
    return bool(token and expected and secrets.compare_digest(token, expected))


def csrf_protect(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not valid_csrf_token(request.form.get("csrf_token")):
            abort(400, "Your form expired or has an invalid security token.")
        return view(*args, **kwargs)

    return wrapped


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def verify_password(password: str) -> bool:
    password_hash = current_app.config["PASSWORD_HASH"]
    return check_password_hash(password_hash, password)
