from flask import render_template, redirect, Blueprint, request, session, url_for
from recommendation import RecommendationLog
import re
import time
from recommendation import SurveyResponse
from database import db
from general import UserCondition, Playlist
import random
from general.basic import is_token_expired, get_refresh_token, generate_playlist, save_tracks_to_playlist
import uuid
from longitudinal import UserPlaylistSession

longitudinal_bp = Blueprint('longitudinal_bp', __name__, template_folder='templates')
session_num = 1


@longitudinal_bp.route('/')
def index():
    return render_template('main.html')


@longitudinal_bp.route('/redirect_from_index')
def redirect_from_index():
    if request.args.get("subject_id"):
        session["subject_id"] = request.args.get("subject_id")
        print(session["subject_id"])

        if session_num == 1:
            return redirect(url_for("longitudinal_bp.inform_consent"))
        elif session_num == 2:
            return redirect(url_for("longitudinal_bp.error_page"))
        elif session_num == 3:
            return redirect(url_for("longitudinal_bp.error_page"))
        elif session_num == 4:
            return redirect(url_for("longitudinal_bp.error_page"))

    return redirect(url_for("longitudinal_bp.error_page"))


@longitudinal_bp.route('/inform_consent')
def inform_consent():
    return render_template('informed_consent.html')


@longitudinal_bp.route('/register')
def register():
    if request.args.get("consent") == "False":
        return redirect(url_for("longitudinal_bp.disagree_informed_consent"))

    if 'subject_id' in session:
        session["share"] = request.args.get("share")
        return redirect(url_for('spotify_basic_bp.login', next_url='longitudinal_bp.redirect_from_main'))
    else:
        return redirect(url_for("longitudinal_bp.error_page"))


@longitudinal_bp.route('/redirect_from_main')
def redirect_from_main():
    # assign study condition
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    if not user_condition:
        condition = random.randint(0, 3)
        # set condition to explore and representative
        condition_text = "vis, representative"
        # condition = 0

        if condition == 1:
            condition_text = "vis, personalized"
        if condition == 2:
            condition_text = "novis, representative"
        if condition == 3:
            condition_text = "novis, personalized"

        user_condition_new = UserCondition(user_id=session["userid"],
                                           timestamp=time.time(),
                                           condition=condition, default=condition_text)
        db.session.add(user_condition_new)
        db.session.commit()

    return redirect(url_for("spotify_basic_bp.msi_survey", redirect_path="longitudinal_bp.select_genre"))


@longitudinal_bp.route('/select_genre')
def select_genre():
    return render_template("select_genre.html")


@longitudinal_bp.route('/error_page')
def error_page():
    return render_template("Error_non_prolificid.html")


@longitudinal_bp.route('/explore_genre')
def explore_genre():
    if session_num == 1:
        # infer the experimental condition
        user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
        user_condition_num = user_condition.condition
        weight = 0.2

        if user_condition_num == 1 or user_condition_num == 3:
            weight = 0.8

        return render_template('explore_genre.html',
                               genre=request.args.get('genre'),
                               weight=weight)
    else:
        return redirect(url_for("longitudinal_bp.error_page"))


@longitudinal_bp.route('/generate_longitudinal_playlist/<genre>')
def generate_longitudinal_playlist(genre):
    rec_id = session['rec_id']

    tracks = request.args.get('tracks')
    track_list = tracks.split(',')

    description = "Recommendations for music genre exploration for " + genre + " in Session " + str(session_num)

    """refresh token"""
    if is_token_expired():
        refresh_token = session["oauth_token"]["refresh_token"]
        get_refresh_token(refresh_token)
    playlist_name = "Session " + str(session_num) + ": " + genre

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

    user_playlist_session = UserPlaylistSession(
        id=str(uuid.uuid4()),
        playlist_id=playlist_id_hash,
        user_id=session["userid"],
        timestamp=timestamp,
        session_num=session_num
    )

    db.session.add(spotify_playlist)
    db.session.add(user_playlist_session)
    db.session.commit()
    return "done"


@longitudinal_bp.route('/last_step')
def last_step():
    # return redirect("https://app.prolific.co/submissions/complete?cc=47904236")
    return render_template("general_last_page.html")