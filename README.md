# Login App (Safe)

A small Flask app that provides a modern login page, validates emails by domain, logs non-sensitive analytics (no passwords) to `analytics.jsonl`, and can redirect with a short-lived JWT or show a success modal.

Features
- Prefill email via shareable `/t/<token>` links stored in `tokens.json`
- Optional domain validation via `ALLOWED_EMAIL_DOMAIN`
- Non-sensitive JSONL logging: events, timestamp, IP, user-agent
- Issues short-lived JWT and redirects to your other site (optional)
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
python app.py add user@organization.net
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

Analytics (management stats)
- The app writes non-sensitive events to `analytics.jsonl` (JSON Lines):
  - token_visit: user clicked/opened their link
  - login_invalid_input / login_failed: user attempted to enter credentials
  - login_success: credentials verified; exposure count proxy
- You can count them quickly, for example in PowerShell:
```
Get-Content analytics.jsonl | % { ($_ | ConvertFrom-Json).event } | Group-Object | Select-Object Name,Count
```


