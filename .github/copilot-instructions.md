# Copilot Instructions for Vinyl Emporium Project

## Architecture Overview

This is a Flask-based web application managing a vinyl record library using the **Chinook SQLite database**. The architecture follows a three-layer pattern:

- **Frontend**: Jinja2 templates with Bootstrap 5.3.1 UI (`templates/`)
- **Backend**: Flask routes in `chouser460.py` with session-based authentication
- **Database**: SQLite with utility functions in `utils/sqlite_utils.py`

Key entry point: Run with `python chouser460.py` (debug mode enabled on port 5000)

## Authentication & Security

- Custom `@login_required` decorator protects routes; unauthenticated requests redirect to `/login`
- Password validation uses MD5 hash + salt: `MD5(password + salt)` compared against `PassHash` in users table
- Sessions stored in Flask session object; login form accepts username and password
- **⚠️ Security Gap**: MD5 is outdated - consider upgrading to bcrypt if adding new user functionality

## Database Patterns

**Connection management** in `utils/sqlite_utils.py`:
- `get_db_connection()` returns connection with `row_factory = sqlite3.Row` for dict-like access
- Always call `conn.close()` in finally blocks; exception handling catches `sqlite3.error`
- Database path: `../db/chinook.db` (relative to utils directory)

**Column naming convention**: Chinook uses CamelCase IDs (`ArtistId`, `GenreId`, `AlbumId`, `MediaTypeId`)

**Query patterns for filtering**:
```python
# Dynamic WHERE clause construction in get_filtered_tracks()
if genre_id:
    query += " AND t.GenreId = ?"
    params.append(genre_id)
```
- Always use parameterized queries (`?` placeholders) to prevent SQL injection
- URLs pass filter params as query strings: `?genre=2&artist=5&media_type=1&album=3`

## Frontend & Templating

- **Base template** (`templates/base.html`): Extends with `{% block main %}` and `{% block footer %}`
- URL generation: Use `{{ url_for('route_name') }}` for links and form actions
- Filter dropdown values should be compared as strings: `{% if selected_genre == g.GenreId|string %}`
- Bootstrap classes used: `.table`, `.table-hover`, `.form-select`, `.btn-primary`, `.badge.bg-info`

## Routing Conventions

- Public routes: `/login`, `/logout`
- Protected routes (require `@login_required`): `/`, `/home`, `/tracks`, `/artists`
- Tracks route stores filter selections in URL: `{{ url_for('tracks', genre=selected_genre, artist=selected_artist, ...) }}`
- Render templates with context variables: `rt("template.html", title=title, lable=lbl, filters=filters, ...)`

## Key Implementation Details

| Component | File | Responsibility |
|-----------|------|-----------------|
| Flask app setup, routes, decorator | `chouser460.py` | Application logic, session management |
| All DB queries | `utils/sqlite_utils.py` | Query execution, data retrieval, validation |
| Track filtering | `get_filtered_tracks()` | Multi-field filtering (genre, artist, media, album) with LIMIT 100 |
| Dropdown population | `get_filter_options()` | Returns dict with genres, artists, media_types, albums |

## Common Patterns to Follow

1. **Error handling**: Try/except with `sqlite3.error`, print error, return False
2. **Parameter ordering in renders**: `rt("template.html", title=title, lable=lbl, ...)` - context variables match template variable names
3. **Form method**: Use `method="GET"` for filters (preserves in URL), `method="POST"` for login
4. **Query string parameters**: Passed via `request.args.get()`

## Known Issues & Technical Notes

- Template variable typo: `lable` (should be `label`) used inconsistently across renders - maintain current naming for compatibility
- Track results limited to 100 rows (LIMIT 100) for performance
- Media type filter param name: `media_type` in querystring but `MediaTypeId` in database
- OLD version exists: `chouser460OLD.py` - do not use

## Development Workflow

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app (runs on http://0.0.0.0:5000 with debug=True)
python chouser460.py

# Access application
# http://localhost:5000/login (start here)
```

Before modifying database queries or adding routes, verify filter mappings in `tracks()` function and test with test database credentials.
