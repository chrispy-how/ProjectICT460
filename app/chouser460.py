from flask import Flask, request, redirect, session, url_for, flash
from flask import render_template as rt
from utils.sqlite_utils import (
    check_login,
    get_filter_options,
    get_filtered_tracks,
    get_track,
    add_track,
    update_track,
    delete_track,
    get_all_artists,
    get_artist,
    get_artist_albums,
    add_artist,
    update_artist,
    delete_artist,
)
import sqlite3
import hashlib
import logging

from werkzeug.serving import WSGIRequestHandler

# ANSI color codes
RESET = "\033[0m"
YELLOW = "\033[33m"
RED = "\033[31m"

class ColorFormatter(logging.Formatter):
    def formatMsg(self, record):
        # Color just the message
        if record.levelno == logging.WARNING:
            record.msg = f"{YELLOW}{record.msg}{RESET}"
        elif record.levelno == logging.ERROR:
            record.msg = f"{RED}{record.msg}{RESET}"
        return super().format(record)

    def format(self, record):
        # Color the LEVEL NAME
        if record.levelno == logging.WARNING:
            record.levelname = f"{YELLOW}{record.levelname}{RESET}"
            record.msg = f"{YELLOW}{record.msg}{RESET}"
        elif record.levelno == logging.ERROR:
            record.levelname = f"{RED}{record.levelname}{RESET}"
            record.msg = f"{RED}{record.msg}{RESET}"

        return super().format(record)

# Apply formatter to the root logger
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().handlers = [handler]
logging.getLogger().setLevel(logging.INFO)

STATIC_LOGS_ENABLED = False
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

title = "James Smith's Vinyl Emporium"
lbl = " Welcome to our Vinyl Emporium "

app = Flask(__name__)
app.secret_key = "APhraseOrSeriesOfRandomCharacters"   # Needed for sessions

# -------------------------
#  LOGIN REQUIRED DECORATOR
# -------------------------
def login_required(func):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# -------------------------
#        LOGIN ROUTES
# -------------------------


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        try:
            # Validate login (no password logging!)
            if check_login(username, password):
                # Retrieve role ID
                from utils.sqlite_utils import get_user_role
                roleid = get_user_role(username)

                # Set session values
                session['user'] = username
                session['roleid'] = roleid

                # Log successful login
                logging.info(f"Successful login for user '{username}' with role ID {roleid}")

                return redirect(url_for('home'))

            else:
                # Log failed login attempt (no password)
                logging.warning(f"Failed login attempt for user '{username}'")

                return rt("login.html",
                          title=title,
                          label=lbl,
                          error="Invalid login")

        except Exception:
            # Log unexpected system error with traceback
            logging.error("Unexpected system error during login", exc_info=True)

            return rt("login.html",
                      title=title,
                      label=lbl,
                      error="System error")

    # GET request
    return rt("login.html", title=title, label=lbl, error=None)
        
"""        
        # Call your DB function
        if check_login(username, password):
            session['user'] = username
            # retrieve role id for session
            from utils.sqlite_utils import get_user_role
            session['roleid'] = get_user_role(username)
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password", "error")


    return rt("login.html", title=title, label=lbl, error=None)
"""

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# -------------------------
#        ROUTES
# -------------------------

@app.route("/")
@app.route("/home")
@login_required
def home():
    return rt("home.html", title=title, label=lbl, content="JSmith Homepage Content")

@app.route("/tracks")
@login_required
def tracks():
    # Get filter values from the URL query string
    genre_id = request.args.get('genre')
    artist_id = request.args.get('artist')
    media_id = request.args.get('media_type')
    album_id = request.args.get('album')

    filters = get_filter_options()
    tracks_list = get_filtered_tracks(genre_id, artist_id, media_id, album_id)

    return rt("tracks.html",
              title=title,
              label=lbl,
              filters=filters,
              tracks=tracks_list,
              selected_genre=genre_id,
              selected_artist=artist_id,
              selected_media=media_id,
              selected_album=album_id)

@app.route("/track_add", methods=["GET", "POST"])
@login_required
def track_add():

    filters = get_filter_options()
    error_msg = None

    if request.method == "POST":
        # Unauthorized attempt
        if session.get('roleid', 99) > 2:            
            logging.warning(
                f"Unauthorized attempt to add a track by user '{session.get('user')}'"
            )
            error_msg = "Not allowed to make changes to data"

        else:
            name = request.form.get("name")
            album = request.form.get("album")
            media = request.form.get("media_type")
            genre = request.form.get("genre")
            milliseconds = request.form.get("milliseconds")
            unit_price = request.form.get("unit_price")

            added = add_track(name, album, media, genre, milliseconds, unit_price)

            if added:
                logging.info(
                    f"Track added successfully by user '{session.get('user')}' "
                    f"(track name: '{name}')"
                )
                flash("Track added successfully", "info")
                return redirect(url_for('tracks'))
            else:
                logging.warning(
                    f"Track add failed for user '{session.get('user')}' "
                    f"(track name: '{name}')"
                )
                flash("Failed to add track", "error")

    return rt("track_add.html",
              title=title,
              label=lbl,
              albums=filters['albums'],
              media_types=filters['media_types'],
              genres=filters['genres'],
              error_msg=error_msg)

@app.route("/track_edit/<int:track_id>", methods=["GET", "POST"])
@login_required
def track_edit(track_id):

    if session.get('roleid', 99) > 2:
        logging.warning(
            f"Unauthorized attempt to ACCESS track_edit for track {track_id} "
            f"by user '{session.get('user')}'"
        )
        flash("Not allowed to access this page", "error")
        return redirect(url_for('tracks'))

    filters = get_filter_options()
    track = get_track(track_id)

    if not track:
        flash("Track not found", "error")
        return redirect(url_for('tracks'))

    error_msg = None

    if request.method == "POST":
        # Unauthorized attempt
        if session.get('roleid', 99) > 2:
            logging.warning(
                f"Unauthorized attempt to edit track {track_id} "
                f"by user '{session.get('user')}'"
            )
            error_msg = "Not allowed to make changes to data"

        else:
            name = request.form.get("name")
            album = request.form.get("album")
            media = request.form.get("media_type")
            genre = request.form.get("genre")
            milliseconds = request.form.get("milliseconds")
            unit_price = request.form.get("unit_price")

            success = update_track(
                track_id, name, album, media, genre, milliseconds, unit_price
            )

            if success:
                logging.info(
                    f"Track {track_id} updated successfully by user '{session.get('user')}' "
                    f"(new name: '{name}')"
                )
                flash("Track updated", "info")
                return redirect(url_for('tracks'))
            else:
                logging.warning(
                    f"Track update failed for track {track_id} "
                    f"by user '{session.get('user')}'"
                )
                flash("Failed to update track", "error")

    return rt(
        "track_edit.html",
        title=title,
        label=lbl,
        track=track,
        albums=filters['albums'],
        media_types=filters['media_types'],
        genres=filters['genres'],
        error_msg=error_msg
    )

@app.route("/track_confirm_delete/<int:track_id>", methods=["GET", "POST"])
@login_required
def track_confirm_delete(track_id):
    error_msg = None

    # Fetch track once for logging and template
    track = get_track(track_id)
    if not track:
        flash("Track not found", "error")
        return redirect(url_for('tracks'))

    track_name = track["Name"] if track else "Unknown"

    if request.method == "POST":
        # Unauthorized attempt
        if session.get('roleid', 99) > 2:
            logging.warning(
                f"Unauthorized attempt to delete track {track_id} "
                f"('{track_name}') by user '{session.get('user')}'"
            )
            error_msg = "Not allowed to make changes to the data"
        else:
            if delete_track(track_id):
                logging.info(
                    f"Track {track_id} ('{track_name}') deleted successfully by user '{session.get('user')}'"
                )
                flash("Track deleted", "info")
                return redirect(url_for('tracks'))
            else:
                logging.warning(
                    f"Track deletion failed for track {track_id} "
                    f"by user '{session.get('user')}'"
                )
                flash("Could not delete track", "error")
                return redirect(url_for('tracks'))

    # GET or POST with error (unauthorized)
    return rt("track_confirm_delete.html",
              title=title,
              label=lbl,
              track=track,
              error_msg=error_msg)

@app.route("/track_delete/<int:track_id>", methods=["POST"])
@login_required
def track_delete(track_id):
    track = get_track(track_id)
    track_name = track.get("Name") if track else "Unknown"

    # Unauthorized attempt
    if session.get('roleid', 99) > 2:
        logging.warning(
            f"Unauthorized attempt to delete track {track_id} "
            f"('{track_name}') by user '{session.get('user')}'"
        )
        flash("Not allowed", "error")
        return redirect(url_for('tracks'))

    # Authorized delete
    if delete_track(track_id):
        logging.info(
            f"Track {track_id} ('{track_name}') deleted successfully "
            f"by user '{session.get('user')}'"
        )
        flash("Track deleted", "info")
    else:
        logging.warning(
            f"Track deletion failed for track {track_id} "
            f"('{track_name}') by user '{session.get('user')}'"
        )
        flash("Could not delete track", "error")

    return redirect(url_for('tracks'))

@app.route("/artists")
@login_required
def artists():
    artist_list = get_all_artists()
    artist_data = []
    for artist in artist_list:
        albums = get_artist_albums(artist[0])
        artist_data.append({
            'ArtistId': artist[0],
            'Name': artist[1],
            'Albums': albums
        })
    return rt("artists.html", title=title, label=lbl, artists=artist_data)

@app.route("/artist_add", methods=["GET", "POST"])
@login_required
def artist_add():
    error_msg = None
    if request.method == "POST":
        if session.get('roleid', 99) > 2:
            logging.warning(
                f"Unauthorized attempt to add an artist by user '{session.get('user')}'"
            )
            error_msg = "Not allowed to make changes to the data"

        else:
            name = request.form.get("name")
            if not name or not name.strip():
                error_msg = "Artist name is required"
            else:
                artist_id = add_artist(name)
                if artist_id:
                    logging.info(
                        f"Artist added successfully by user '{session.get('user')}' "
                        f"(Artist name: '{name}')"
                    )                    
                    flash("Artist added successfully", "info")
                    return redirect(url_for('artists'))
                else:
                    error_msg = "Failed to add artist"
    return rt("artist_add.html", title=title, label=lbl, error_msg=error_msg)

@app.route("/artist_edit/<int:artist_id>", methods=["GET", "POST"])
@login_required
def artist_edit(artist_id):
    artist = get_artist(artist_id)
    if not artist:
        flash("Artist not found", "error")
        return redirect(url_for('artists'))
    error_msg = None
    if request.method == "POST":
        if session.get('roleid', 99) > 2:
            logging.warning(
                f"Unauthorized attempt to edit an artist by user '{session.get('user')}'"
            )
            error_msg = "Not allowed to make changes to the data"
        else:
            name = request.form.get("name")
            if not name or not name.strip():
                error_msg = "Artist name is required"
            else:
                if update_artist(artist_id, name):
                    logging.info(
                        f"Artist {artist_id} updated successfully by user '{session.get('user')}' "
                        f"(new name: '{name}')"
                    )                    
                    flash("Artist updated", "info")
                    return redirect(url_for('artists'))
                else:
                    error_msg = "Failed to update artist"
    return rt("artist_edit.html", title=title, label=lbl, artist=artist, error_msg=error_msg)

@app.route("/artist_confirm_delete/<int:artist_id>", methods=["GET", "POST"])
@login_required
def artist_confirm_delete(artist_id):
    error_msg = None

    # Fetch artist early so we can log with the name
    artist = get_artist(artist_id)
    artist_name = artist["Name"] if artist else "Unknown"

    if request.method == "POST":
        if session.get('roleid', 99) > 2:
            logging.warning(
                f"Unauthorized attempt to delete artist {artist_id} "
                f"('{artist_name}') by user '{session.get('user')}'"
            )
            error_msg = "Not allowed to make changes to the data"

        else:
            if delete_artist(artist_id):
                logging.info(
                    f"Artist {artist_id} ('{artist_name}') deleted successfully "
                    f"by user '{session.get('user')}'"
                )
                flash("Artist deleted", "info")
                return redirect(url_for('artists'))
            else:
                logging.warning(
                    f"Artist deletion failed for artist {artist_id} "
                    f"('{artist_name}') by user '{session.get('user')}'"
                )
                flash("Cannot delete artist (has albums or not found)", "error")
                return redirect(url_for('artists'))

    # GET request or POST with error
    if not artist:
        flash("Artist not found", "error")
        return redirect(url_for('artists'))

    return rt("artist_confirm_delete.html",
              title=title,
              label=lbl,
              artist=artist,
              error_msg=error_msg)

# legacy POST delete
@app.route("/artist_delete/<int:artist_id>", methods=["POST"])
@login_required
def artist_delete(artist_id):
    if delete_artist(artist_id):
        flash("Artist deleted", "info")
    else:
        flash("Cannot delete artist (has albums or not found)", "error")
    return redirect(url_for('artists'))

@app.route("/log_unauthorized_delete_attempt/<int:track_id>", methods=["POST"])
@login_required
def log_unauthorized_delete_attempt(track_id):
    track = get_track(track_id)
    track_name = track["Name"] if track else "Unknown"

    logging.error(
        f"Unauthorized click on disabled delete button for track {track_id} "
        f"('{track_name}') by user '{session.get('user')}'"
    )

    # Return an empty response so the browser stays quiet
    return ("", 204)

@app.route("/log_unauthorized_edit_attempt/<int:track_id>", methods=["POST"])
@login_required
def log_unauthorized_edit_attempt(track_id):
    track = get_track(track_id)
    track_name = track["Name"] if track else "Unknown"

    logging.error(
        f"Unauthorized click on disabled edit button for artist {track_id} "
        f"('{track_name}') by user '{session.get('user')}'"
    )

    # Return an empty response so the browser stays quiet
    return ("", 204)
# -------------------------
#        MAIN making some changes so I can commit and push to github and show the new logs with colors
# -------------------------

class NoStaticLogs(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        # Only suppress static file logs
        if self.path.startswith('/static/'):
            return
        super().log_request(code, size)

class ConditionalStaticLogFilter(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        # Only suppress static logs when the flag is False
        if not STATIC_LOGS_ENABLED and self.path.startswith('/static/'):
            return
        super().log_request(code, size)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, request_handler=ConditionalStaticLogFilter)