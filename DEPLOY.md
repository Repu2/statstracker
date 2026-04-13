# Deployment Guide

## Quick start

```bash
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:application
```

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRIMTRACKER_SECRET` | Flask session secret (use a random string) | `dev-change-me` |
| `SCRIMTRACKER_DB` | SQLite database path | `scrimtracker.sqlite3` |
| `FLASK_DEBUG` | Set to `true` only for local dev | `false` |

## PythonAnywhere

1. **Upload** the `version1` folder contents to your project directory (e.g. `/home/yourusername/mysite/`).

2. **Create a virtualenv** (Consoles → Bash):
   ```bash
   mkvirtualenv --python=/usr/bin/python3.11 mysite-virtualenv
   pip install -r requirements.txt
   ```

3. **Configure the Web app** (Web tab):
   - Add a new web app → Manual configuration
   - Set **Virtualenv** to your venv path (e.g. `mysite-virtualenv`)
   - Click the **WSGI configuration file** link and replace its contents with the contents of `wsgi.py` (or ensure it points to your project’s `wsgi.py`)

4. **WSGI file** must expose `application`. Our `wsgi.py` already does this.

5. **Environment variables** (Web tab → Code section): add `SCRIMTRACKER_SECRET` and optionally `SCRIMTRACKER_DB` (default: `scrimtracker.sqlite3` in the project directory).

6. **Reload** the web app from the Web tab.

## Security

- Set `SCRIMTRACKER_SECRET` to a strong random value in production.
- Change the login password in `app.py` before deploying (or move it to env/config).
- Do not set `FLASK_DEBUG=true` in production.
