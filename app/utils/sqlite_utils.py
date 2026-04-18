import sqlite3
import hashlib
import os

# -----------------------------------
#  DATABASE CONNECTION FUNCTION
# -----------------------------------
def get_db_connection():
    """Return a connection to the chinook.db SQLite database."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    db_path = os.path.join(parent_dir, '..', 'db', 'chinook.db')

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # allows dict-like access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# -----------------------------------
#  LOGIN VALIDATION FUNCTION
# -----------------------------------
def check_login(username, password):
    """
    Receives a username and password.
    Attempts to validate against the `employees` table first (matching on lower(Email)).
    If `PassSalt`/`PassHash` are not present in `employees`, falls back to the
    legacy `users` table.
    Returns True if MD5(password + salt) matches stored hash. Returns False otherwise.

    Note: role information is retrieved separately by `get_user_role`.
    """

    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        # First try employees table (match by email lower-cased)
        try:
            cur.execute("SELECT PassSalt, PassHash FROM employees WHERE lower(Email) = ?", (username.lower(),))
            row = cur.fetchone()
        except sqlite3.OperationalError:
            # employees table may not have PassSalt/PassHash columns; fall through to users
            row = None

        # Fallback to users table if no row found in employees
        if not row:
            try:
                cur.execute("SELECT PassSalt, PassHash FROM users WHERE UserName = ?", (username.lower(),))
                row = cur.fetchone()
            except sqlite3.Error:
                row = None

        if row:
            pass_salt, pass_hash = row
            # combine password and salt, then compare the md5 hash
            combined = password + pass_salt
            md5_hash = hashlib.md5(combined.encode()).hexdigest()
            return md5_hash == pass_hash
        return False
    except sqlite3.Error as e:
        print(f"Error querying database: {e}")
        return False
    finally:
        conn.close()

#------------------
# Filtering Tracks
#------------------
def get_filter_options():
    """Fetches lists for the dropdown menus."""
    conn = get_db_connection()
    if not conn:
        return [], [], [], []
    try:
        cur = conn.cursor()
        # Fetching all options for the dropdowns
        genres = cur.execute("SELECT GenreId, Name FROM genres ORDER BY Name").fetchall()
        artists = cur.execute("SELECT ArtistId, Name FROM artists ORDER BY Name").fetchall()
        media_types = cur.execute("SELECT MediaTypeId, Name FROM media_types ORDER BY Name").fetchall()
        albums = cur.execute("SELECT AlbumId, Title FROM albums ORDER BY Title").fetchall()
        conn.close()
        return {"genres": genres, "artists": artists, "media_types": media_types, "albums": albums}
    except sqlite3.Error as e:
        print(f"Error gathering track options")
        return False
    finally:
        conn.close()

def get_filtered_tracks(genre_id=None, artist_id=None, media_id=None, album_id=None):
    """Fetches tracks based on user-selected criteria."""
    conn = get_db_connection()
    cur = conn.cursor()
    if not conn:
        return False
    try:
        query = """
            SELECT t.TrackId, t.Name as TrackName, 
            a.Name as ArtistName, 
            al.Title as AlbumTitle, 
            g.Name as Genre
            FROM tracks t
            JOIN albums al ON t.AlbumId = al.AlbumId
            JOIN artists a ON al.ArtistId = a.ArtistId
            JOIN genres g ON t.GenreId = g.GenreId
            WHERE 1=1
        """
        params = []
        
        if genre_id:
            query += " AND t.GenreId = ?"
            params.append(genre_id)
        if artist_id:
            query += " AND a.ArtistId = ?"
            params.append(artist_id)
        if media_id:
            query += " AND t.MediaTypeId = ?"
            params.append(media_id)
        if album_id:
            query += " AND t.AlbumId = ?"
            params.append(album_id)    

        query += " LIMIT 100" # Keep it performant
        results = cur.execute(query, params).fetchall()
    except sqlite3.error as e:
        print(f"Error gathering track information")
        return False
    finally:
        conn.close()
    return results

# ------------------
#  TRACK CRUD
# ------------------

def get_track(track_id):
    """Return a single track row by TrackId."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        row = cur.execute("SELECT * FROM tracks WHERE TrackId = ?", (track_id,)).fetchone()
        return row
    except sqlite3.Error as e:
        print(f"Error fetching track: {e}")
        return None
    finally:
        conn.close()


def add_track(name, album_id, media_type_id, genre_id, milliseconds, unit_price):
    """Insert a new track and return its TrackId."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO tracks
               (Name, AlbumId, MediaTypeId, GenreId, Milliseconds, UnitPrice)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, album_id, media_type_id, genre_id, milliseconds, unit_price),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding track: {e}")
        return None
    finally:
        conn.close()


def update_track(track_id, name, album_id, media_type_id, genre_id, milliseconds, unit_price):
    """Update an existing track's details."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE tracks SET Name=?, AlbumId=?, MediaTypeId=?, GenreId=?,
               Milliseconds=?, UnitPrice=? WHERE TrackId = ?""",
            (name, album_id, media_type_id, genre_id, milliseconds, unit_price, track_id),
        )
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating track: {e}")
        return False
    finally:
        conn.close()


def delete_track(track_id):
    """Remove a track by its ID."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM tracks WHERE TrackId = ?", (track_id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting track: {e}")
        return False
    finally:
        conn.close()

# ------------------
#  ARTIST CRUD
# ------------------

def get_all_artists():
    """Return all artists, ordered by name."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT ArtistId, Name FROM artists ORDER BY Name"
        ).fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching artists: {e}")
        return []
    finally:
        conn.close()


def get_artist(artist_id):
    """Return a single artist by ID."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        row = cur.execute(
            "SELECT ArtistId, Name FROM artists WHERE ArtistId = ?",
            (artist_id,)
        ).fetchone()
        return row
    except sqlite3.Error as e:
        print(f"Error fetching artist: {e}")
        return None
    finally:
        conn.close()


def get_artist_albums(artist_id):
    """Return all albums by a given artist."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        rows = cur.execute(
            """SELECT AlbumId, Title FROM albums
               WHERE ArtistId = ? ORDER BY Title""",
            (artist_id,)
        ).fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching artist albums: {e}")
        return []
    finally:
        conn.close()


def add_artist(name):
    """Insert a new artist and return its ArtistId."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO artists (Name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding artist: {e}")
        return None
    finally:
        conn.close()


def update_artist(artist_id, name):
    """Update an artist's name."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE artists SET Name = ? WHERE ArtistId = ?",
            (name, artist_id)
        )
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating artist: {e}")
        return False
    finally:
        conn.close()


def delete_artist(artist_id):
    """Delete an artist (only if no albums reference it)."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        # Check if artist has albums
        cur.execute("SELECT COUNT(*) FROM albums WHERE ArtistId = ?", (artist_id,))
        if cur.fetchone()[0] > 0:
            print("Cannot delete artist with albums")
            return False
        cur.execute("DELETE FROM artists WHERE ArtistId = ?", (artist_id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting artist: {e}")
        return False
    finally:
        conn.close()


def get_user_role(username):
    """Return RoleId for a given username (lowercased) or None."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT RoleId FROM users WHERE lower(UserName)=?", (username.lower(),))
        row = cur.fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Error getting user role: {e}")
        return None
    finally:
        conn.close()


