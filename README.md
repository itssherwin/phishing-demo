Keepa Login App (Safe)

A small Flask app that provides a modern login page, validates `@keepa.ir` emails, logs non-sensitive analytics (no passwords) to `analytics.jsonl`, and redirects to another site with a short-lived JWT on successful login.

Features
- Prefill email via shareable `/t/<token>` links stored in `tokens.json`
- Validates `@keepa.ir` emails
- Non-sensitive JSONL logging: events, timestamp, IP, user-agent
- Issues short-lived JWT and redirects to your other site
- Modern purple/blue theme

Install
```
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run (dev)
```
$env:FLASK_SECRET_KEY = "dev-secret"
$env:JWT_SECRET = "dev-jwt-secret"
$env:OTHER_SITE_URL = "https://your-other-site.example/consume"  # optional if not redirecting
$env:ALLOWED_EMAIL_DOMAIN = "organization.net"                    # optional domain enforcement
$env:AUTH_MODE = "demo"            # or allow_all
$env:DEMO_PASSWORD = "demo1234"    # if AUTH_MODE=demo
python app.py
```

Open `http://127.0.0.1:5000`.

Token links
Create a tokenized link that prefills the email on the login form:
```
python app.py add user@keepa.ir
```
This prints a shareable link like `http://127.0.0.1:5000/t/<token>`.

List or delete tokens:
```
python app.py list
python app.py delete <token>
```

Integrating the redirect
Your other site should verify the JWT using the same `JWT_SECRET`, check `iss`, `aud`, and `exp`, and then sign the user in based on `sub` (email).

Notes
- Passwords are never written to logs.
- Replace `verify_credentials` in `app.py` with your real auth.

Publishing guidance
- Copy sample files and edit for your environment:
  - `cp site_config.sample.json site_config.json`
  - `cp users.sample.json users.json`
  - `cp tokens.sample.json tokens.json`
- Environment variable `ALLOWED_EMAIL_DOMAIN` controls allowed email domain.
- `.gitignore` excludes runtime/sensitive files from version control.


