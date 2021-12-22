from flask import render_template, redirect, Blueprint, request, session, url_for
from recommendation import RecommendationLog
import re
import time
from recommendation import SurveyResponse
from database import db
from general import UserCondition
import random

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