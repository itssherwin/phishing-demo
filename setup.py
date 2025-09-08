import json
import shutil
from pathlib import Path
import argparse
import os
import bcrypt


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
SITE_CONFIG_FILE = BASE_DIR / "site_config.json"
USERS_FILE = BASE_DIR / "users.json"
ENV_FILE = BASE_DIR / ".env"
TOKENS_FILE = BASE_DIR / "tokens.json"


def ensure_files():
    if not SITE_CONFIG_FILE.exists():
        SITE_CONFIG_FILE.write_text(json.dumps({
            "rtl": False,
            "theme": {"yellow": "#facc15"}
        }, indent=2), encoding="utf-8")
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}", encoding="utf-8")
    # Do not create tokens.json automatically in setup to avoid leaking examples


def set_rtl(enabled: bool):
    cfg = json.loads(SITE_CONFIG_FILE.read_text(encoding="utf-8") or "{}")
    cfg["rtl"] = bool(enabled)
    SITE_CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("RTL set to:", enabled)


def set_theme_yellow(hex_color: str):
    cfg = json.loads(SITE_CONFIG_FILE.read_text(encoding="utf-8") or "{}")
    theme = cfg.get("theme", {})
    theme["yellow"] = hex_color
    cfg["theme"] = theme
    SITE_CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Theme yellow set to:", hex_color)


def set_allowed_domain(domain: str):
    domain = domain.strip()
    if not domain or "@" in domain:
        raise SystemExit("Provide a bare domain like organization.net")
    # Write to a simple .env-style file (optional convenience)
    lines = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        lines = [ln for ln in lines if not ln.startswith("ALLOWED_EMAIL_DOMAIN=")]
    lines.append(f"ALLOWED_EMAIL_DOMAIN={domain}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("ALLOWED_EMAIL_DOMAIN set to:", domain)


def customize_template(source_html: Path):
    if not source_html.exists():
        raise FileNotFoundError(f"Template not found: {source_html}")
    target = TEMPLATES_DIR / "login.html"
    shutil.copyfile(source_html, target)
    print("Copied template to:", target)


def add_user(email: str, password_hash: str):
    data = json.loads(USERS_FILE.read_text(encoding="utf-8") or "{}")
    data[email] = {"password_hash": password_hash}
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("User added:", email)


def remove_user(email: str):
    data = json.loads(USERS_FILE.read_text(encoding="utf-8") or "{}")
    if email in data:
        del data[email]
        USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print("User removed:", email)
    else:
        print("User not found:", email)


def make_bcrypt_hash(password: str) -> None:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    print(hashed)


def init_samples():
    # Copy sample JSONs if they exist
    for src_name, dst in (
        ("site_config.sample.json", SITE_CONFIG_FILE),
        ("users.sample.json", USERS_FILE),
        ("tokens.sample.json", TOKENS_FILE),
    ):
        src = BASE_DIR / src_name
        if src.exists() and not dst.exists():
            shutil.copyfile(src, dst)
            print("Created", dst.name, "from", src.name)


def main():
    ensure_files()
    p = argparse.ArgumentParser(description="Setup/customization for the login app")
    sub = p.add_subparsers(dest="cmd")

    p_rtl = sub.add_parser("rtl", help="Enable or disable RTL")
    p_rtl.add_argument("value", choices=["on", "off"], help="Set RTL on/off")

    p_yellow = sub.add_parser("yellow", help="Set yellow accent color (hex)")
    p_yellow.add_argument("hex", help="#RRGGBB or CSS color")

    p_domain = sub.add_parser("domain", help="Set allowed email domain (writes .env)")
    p_domain.add_argument("domain", help="e.g. organization.net")

    p_tmpl = sub.add_parser("template", help="Replace login template with custom HTML")
    p_tmpl.add_argument("path", help="Path to your HTML file")

    p_add = sub.add_parser("add-user", help="Add user with precomputed bcrypt hash")
    p_add.add_argument("email")
    p_add.add_argument("password_hash")

    p_rm = sub.add_parser("remove-user", help="Remove a user")
    p_rm.add_argument("email")

    p_hash = sub.add_parser("make-hash", help="Print bcrypt hash for a password")
    p_hash.add_argument("password")

    sub.add_parser("init-samples", help="Copy *sample.json files to working JSONs if missing")

    args = p.parse_args()
    if args.cmd == "rtl":
        set_rtl(args.value == "on")
    elif args.cmd == "yellow":
        set_theme_yellow(args.hex)
    elif args.cmd == "domain":
        set_allowed_domain(args.domain)
    elif args.cmd == "template":
        customize_template(Path(args.path))
    elif args.cmd == "add-user":
        add_user(args.email, args.password_hash)
    elif args.cmd == "remove-user":
        remove_user(args.email)
    elif args.cmd == "make-hash":
        make_bcrypt_hash(args.password)
    elif args.cmd == "init-samples":
        init_samples()
    else:
        p.print_help()


if __name__ == "__main__":
    main()


