# MovieBoat

## Cursor Cloud specific instructions

### Overview
MovieBoat (电影船) is a Chinese-language paid video streaming platform built with Flask. It is a single-service monolithic app with an SQLite database (file-based, no external DB server required).

### Running the app
```
python3 main.py
```
Runs on `http://localhost:8080` with debug mode enabled.

### Key compatibility notes
- The `requirements.txt` pins very old package versions (Flask 0.12.2, Babel 2.4.0, etc.) that are **incompatible with Python 3.12+**. The update script installs compatible transitive dependency versions after `pip install -r requirements.txt`:
  - `Jinja2==2.11.3`, `MarkupSafe==1.1.1` (Flask 0.12.2 requires `from jinja2 import Markup`)
  - `Werkzeug==0.16.1` (Flask 0.12.2 API compatibility)
  - `itsdangerous==1.1.0` (Flask 0.12.2 uses `itsdangerous.json`)
  - `click==7.1.2` (Flask 0.12.2 compatibility)
  - `SQLAlchemy==1.4.54` (Flask-SQLAlchemy 2.x URL mutability)
  - `Flask-SQLAlchemy==2.5.1` (fixes `info.database` attribute error with SQLAlchemy 1.4)
  - `Babel>=2.10` (Babel 2.4.0 uses removed `collections.MutableMapping` in Python 3.10+)

### Database
- SQLite file at `data.sqlite3` in the project root. Created via `db.create_all()` in the app context.
- To recreate: delete `data.sqlite3`, then run `python3 -c "from app import app, db; import models; app.app_context().push(); db.create_all()"`.
- The `init_db.py` seeder requires `pymongo` and `faker` (not in `requirements.txt`) and a MongoDB instance; for local dev, seed data directly via Python/SQLAlchemy.

### Frontend CDN dependency
- jQuery is loaded from `http://upcdn.b0.upaiyun.com` (a Chinese CDN), which is not accessible from most cloud environments. This means AJAX-based features (registration, login, purchase buttons) won't work in the browser UI. Use `curl` or direct API calls to test these endpoints. The Semantic UI CSS/JS are served locally from `/static/semantic/`.

### No automated tests
This codebase has no test suite. Verify functionality via `curl` against the running server or manual browser testing.

### No linter configuration
No linting tools are configured in this project.
