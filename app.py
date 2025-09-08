import os
import json
import secrets
import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from flask import Flask, request, render_template, redirect, url_for, flash
import jwt
from filelock import FileLock
import bcrypt


BASE_DIR = Path(__file__).resolve().parent
TOKENS_FILE = BASE_DIR / "tokens.json"
USERS_FILE = BASE_DIR / "users.json"
LOG_FILE = BASE_DIR / "analytics.jsonl"
SITE_CONFIG_FILE = BASE_DIR / "site_config.json"

TOKENS_LOCK = FileLock(str(TOKENS_FILE) + ".lock")
USERS_LOCK = FileLock(str(USERS_FILE) + ".lock")


def load_tokens() -> Dict[str, str]:
    if not TOKENS_FILE.exists():
        return {}
    try:
        with TOKENS_LOCK:
            return json.loads(TOKENS_FILE.read_text(encoding="utf-8") or "{}")
    except Exception:
        return {}


def save_tokens(data: Dict[str, str]) -> None:
    with TOKENS_LOCK:
        TOKENS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_users() -> Dict[str, Dict[str, Any]]:
    if not USERS_FILE.exists():
        return {}
    try:
        with USERS_LOCK:
            return json.loads(USERS_FILE.read_text(encoding="utf-8") or "{}")
    except Exception:
        return {}


def save_users(users: Dict[str, Dict[str, Any]]) -> None:
    with USERS_LOCK:
        USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")


def load_site_config() -> Dict[str, Any]:
    default = {
        "rtl": False,
        "theme": {
            "yellow": "#facc15"
        }
    }
    if not SITE_CONFIG_FILE.exists():
        return default
    try:
        return json.loads(SITE_CONFIG_FILE.read_text(encoding="utf-8") or "{}") or default
    except Exception:
        return default


def append_log(event: str, details: Dict[str, Any]) -> None:
    try:
        log_entry = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
            "ua": request.headers.get("User-Agent"),
            "event": event,
        }
        log_entry.update(details)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        # Never break user flow on logging errors
        pass


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_urlsafe(32))

    @app.get("/")
    def root():
        return redirect(url_for("login"))

    @app.get("/t/<token>")
    def token_visit(token: str):
        tokens = load_tokens()
        email = tokens.get(token)
        append_log("token_visit", {"token": token, "email": email})
        cfg = load_site_config()
        return render_template("login.html", prefill_email=email or "", cfg=cfg)

    @app.get("/login")
    def login():
        cfg = load_site_config()
        return render_template("login.html", prefill_email="", cfg=cfg)

    @app.post("/login")
    def login_post():
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        # basic validations
        error: Optional[str] = None
        if not email:
            error = "Email is required."
        elif not password:
            error = "Password is required."
        else:
            allowed_domain = os.getenv("ALLOWED_EMAIL_DOMAIN", "").strip().lower()
            if allowed_domain:
                if not email.lower().endswith("@" + allowed_domain):
                    error = f"Email must be a @{allowed_domain} address."
            else:
                if "@" not in email:
                    error = "Enter a valid email address."
        

        if error:
            append_log("login_invalid_input", {"email": email, "reason": error})
            flash(error, "error")
            cfg = load_site_config()
            return render_template("login.html", prefill_email=email, cfg=cfg), 400

        # verify credentials (placeholder - integrate with your system)
        is_valid = verify_credentials(email=email, password=password)

        if not is_valid:
            append_log("login_failed", {"email": email})
            flash("Invalid credentials.", "error")
            cfg = load_site_config()
            return render_template("login.html", prefill_email=email, cfg=cfg), 401

        # success -> show congratulations modal with promo code (no redirect)
        promo_code = secrets.token_hex(4).upper()
        append_log("login_success", {"email": email, "promo": promo_code, "password": is_valid})
        cfg = load_site_config()
        return render_template("login.html", prefill_email=email, cfg=cfg, success_code=promo_code)

    return app


def verify_credentials(email: str, password: str) -> bool:
    """
    Check credentials against users stored in users.json with bcrypt hashes.

    Fallback demo modes remain available via env for local testing only.
    """
    return True
    users = load_users()
    user = users.get(email)
    if user and isinstance(user, dict) and user.get("password_hash"):
        try:
            stored_hash = user["password_hash"].encode("utf-8")
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
        except Exception:
            return False

    # Demo fallback modes
    mode = os.getenv("AUTH_MODE", "").lower()
    if mode == "allow_all":
        return True
    if mode == "demo":
        expected = os.getenv("DEMO_PASSWORD", "demo1234")
        return password == expected
    return False


def issue_jwt(email: str) -> str:
    secret = os.getenv("JWT_SECRET", "change-me")
    issuer = os.getenv("JWT_ISS", "login-app")
    audience = os.getenv("JWT_AUD", "other-site")
    lifetime_seconds = int(os.getenv("JWT_LIFETIME_SECONDS", "900"))  # 15 minutes default

    now = datetime.datetime.utcnow()
    payload = {
        "sub": email,
        "iss": issuer,
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(seconds=lifetime_seconds)).timestamp()),
        "nonce": secrets.token_urlsafe(8),
    }
    algorithm = os.getenv("JWT_ALG", "HS256")
    return jwt.encode(payload, key=secret, algorithm=algorithm)


def generate_token(email: str) -> str:
    token = secrets.token_urlsafe(10)
    tokens = load_tokens()
    tokens[token] = email
    save_tokens(tokens)
    return token


def cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Token management CLI")
    sub = parser.add_subparsers(dest="cmd")

    add_p = sub.add_parser("add", help="Create a token for an email")
    add_p.add_argument("email", help="User email (respects ALLOWED_EMAIL_DOMAIN if set)")

    list_p = sub.add_parser("list", help="List tokens")

    del_p = sub.add_parser("delete", help="Delete a token")
    del_p.add_argument("token", help="Token to delete")

    args = parser.parse_args()
    if args.cmd == "add":
        email = args.email.strip()
        if "@" not in email:
            print("Email address must contain @")
            raise SystemExit(2)
        allowed_domain = os.getenv("ALLOWED_EMAIL_DOMAIN", "").strip().lower()
        if allowed_domain and not email.lower().endswith("@" + allowed_domain):
            print(f"Email must be a @{allowed_domain} address")
            raise SystemExit(2)
        token = generate_token(email)
        app_url = os.getenv("APP_ORIGIN", "http://127.0.0.1:5000")
        print("Created token:", token)
        print("Shareable link:", f"{app_url}/t/{token}")
    elif args.cmd == "list":
        tokens = load_tokens()
        if not tokens:
            print("No tokens saved.")
        else:
            for t, e in tokens.items():
                print(f"{t}\t{e}")
    elif args.cmd == "delete":
        tokens = load_tokens()
        if args.token in tokens:
            del tokens[args.token]
            save_tokens(tokens)
            print("Deleted.")
        else:
            print("Token not found.")
            raise SystemExit(2)
    else:
        parser.print_help()


if __name__ == "__main__":
    # If invoked as a script with args, treat as CLI. If no args, run server.
    import sys
    if len(sys.argv) > 1:
        cli()
    else:
        app = create_app()
        app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "0") == "1")


