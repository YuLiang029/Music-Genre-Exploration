from flask import render_template, redirect, Blueprint, request, session, url_for
import time
from database import db
from general import UserCondition
import random
from longitudinal import UserPlaylistSession
"""
Blueprint for session 1
"""

session1_bp = Blueprint('session1_bp', __name__, template_folder='templates')


@session1_bp.route('/')
def index():
    session["session_num"] = 1
    return render_template('main.html')


@session1_bp.route('/session_register')
def session_register():
    if request.args.get("PROLIFIC_PID"):
        session["subject_id"] = request.args.get("PROLIFIC_PID")
        print(session["subject_id"])

        # Check if the playlist has already been generated
        user_playlist_session = UserPlaylistSession.query.filter_by(
            user_id=session["subject_id"], session_num=session["session_num"]).first()

        if not user_playlist_session:
            return redirect(url_for("session1_bp.inform_consent"))

        return redirect(url_for("long_bp.error_repeat_answer"))

    return redirect(url_for("long_bp.error_page"))


@session1_bp.route('/inform_consent')
def inform_consent():
    return render_template('informed_consent.html')


@session1_bp.route('/register_informed_consent')
def register_informed_consent():
    if request.args.get("consent") == "False":
        return redirect(url_for("session1_bp.disagree_informed_consent"))

    if 'subject_id' in session:
        session["share"] = request.args.get("share")
        return redirect(url_for('spotify_basic_bp.login', next_url='session1_bp.assign_condition'))

    return redirect(url_for("long_bp.error_page"))


@session1_bp.route('/disagree_informed_consent')
def disagree_informed_consent():
    return render_template("Error_inform_consent.html")


@session1_bp.route('/assign_condition')
def assign_condition():
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

    return redirect(url_for("spotify_basic_bp.msi_survey", redirect_path="session1_bp.select_genre"))


@session1_bp.route('/select_genre')
def select_genre():
    return render_template("select_genre.html")


@session1_bp.route('/explore_genre')
def explore_genre():
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    if not user_condition:
        return redirect(url_for("long_bp.error_page"))

    user_condition_num = user_condition.condition

    # infer the experimental condition
    weight = 0.2

    if user_condition_num == 1 or user_condition_num == 3:
        weight = 0.8

    return render_template('explore_genre.html',
                           genre=request.args.get('genre'),
                           weight=weight)

