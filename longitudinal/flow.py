from flask import render_template, redirect, Blueprint, request, session, url_for
import time
from database import db
from general import UserCondition, Playlist
from general.basic import is_token_expired, get_refresh_token, generate_playlist, save_tracks_to_playlist
import uuid
from longitudinal import UserPlaylistSession
from recommendation import RecommendationLog

long_bp = Blueprint('long_bp', __name__, template_folder='templates')


@long_bp.route('/generate_longitudinal_playlist/<genre>')
def generate_longitudinal_playlist(genre):
    rec_id = session['rec_id']

    recommendation_log = RecommendationLog.query.filter_by(id=session["rec_id"]).first()
    recommendation_log.stop_ts = time.time()
    db.session.commit()

    tracks = request.args.get('tracks')
    weight = request.args.get('weight')

    track_list = tracks.split(',')

    description = "Recommendations for music genre exploration for " + genre + " in Session " + str(
        session["session_num"])

    """refresh token"""
    if is_token_expired():
        refresh_token = session["oauth_token"]["refresh_token"]
        get_refresh_token(refresh_token)
    playlist_name = "Session " + str(session["session_num"]) + ": " + genre

    playlist_id, playlist_url = generate_playlist(name=playlist_name, description=description)
    playlist_url = save_tracks_to_playlist(playlist_id, playlist_url, track_list)
    print(playlist_id)
    print(playlist_url)

    playlist_id_hash = str(uuid.uuid4())
    timestamp = time.time()

    spotify_playlist = Playlist(
        id=playlist_id_hash,
        name=playlist_name,
        description=description,
        rec_id=rec_id,
        timestamp=timestamp,
        user_id=session["userid"],
        session_id=session["id"])
    db.session.add(spotify_playlist)
    db.session.commit()

    user_playlist_session = UserPlaylistSession(
        id=str(uuid.uuid4()),
        playlist_id=playlist_id_hash,
        rec_id=rec_id,
        user_id=session["userid"],
        timestamp=timestamp,
        session_num=session["session_num"],
        weight=weight
    )

    db.session.add(user_playlist_session)
    db.session.commit()
    session["playlist_url"] = playlist_url
    return "done"


@long_bp.route('/error_page')
def error_page():
    return render_template('Error_long.html',
                           shown_message="Oops, we could not get your Prolific ID. "
                                         "Please try the survey again with the link with your Prolific ID")


@long_bp.route('/error_repeat_answer')
def error_repeat_answer():
    return render_template('Error_long.html',
                           shown_message="Oops, you cannot participate this session twice. "
                                         "You have already finished this session. ")


@long_bp.route('/last_step')
def last_step():
    # return redirect("https://app.prolific.co/submissions/complete?cc=47904236")
    return render_template("last_page_long.html", playlist_url=session["playlist_url"])
