from flask import render_template, redirect, Blueprint, request, session, url_for
import time
from database import db
from general import UserCondition
import random
from longitudinal import UserPlaylistSession
from recommendation import SurveyResponse, RecommendationLog
import re

"""
Blueprint for session 2
"""

session2_bp = Blueprint('session2_bp', __name__, template_folder='templates')


@session2_bp.route('/')
def index():
    session["session_num"] = 4
    return render_template('main.html')


@session2_bp.route('/session_register')
def session_register():
    if request.args.get("subject_id"):
        session["subject_id"] = request.args.get("subject_id")

        # Check if the playlist has already been generated
        user_playlist_session = UserPlaylistSession.query.filter_by(
            user_id=session["subject_id"], session_num=session["session_num"]).first()

        if not user_playlist_session:
            return redirect(url_for('spotify_basic_bp.login',
                                    next_url='session2_bp.pre_survey'))

        return redirect(url_for("long_bp.error_repeat_answer"))

    return redirect(url_for("long_bp.error_page"))


@session2_bp.route('/pre_survey', methods=["GET", "POST"])
def pre_survey():
    rec_id = UserPlaylistSession.query.filter_by(user_id=session["userid"],
                                                 ).order_by(UserPlaylistSession.session_num.desc()).first().rec_id
    if request.method == "GET":
        recommendation_log = RecommendationLog.query.filter_by(id=rec_id).first()
        responses = recommendation_log.survey_response
        surveydata = {}

        for responseitem in responses:
            m = re.match(r"^([^\[]*)\[([0-9]+)\]$", responseitem.item_id)
            if m:
                print(responseitem.item_id + " " + m.group(1))
                print(m.group(1))
                if m.group(1) in surveydata:
                    surveydata[m.group(1)][m.group(2)] = responseitem.value
                else:
                    surveydata[m.group(1)] = {}
                    surveydata[m.group(1)][m.group(2)] = responseitem.value
            else:
                surveydata[responseitem.item_id] = responseitem.value

        survey = {
            "showProgressBar": "top",
            "pages": [
                {"questions": [
                    {
                        "type": "matrix",
                        "name": "help",
                        "title": "Please indicate to what extent you agree or disagree with each statement about "
                                 "the playlist you just created",
                        "isAllRowRequired": "true",
                        "columns": [
                            {"value": 1, "text": "Completely Disagree"},
                            {"value": 2, "text": "Strongly Disagree"},
                            {"value": 3, "text": "Disagree"},
                            {"value": 4, "text": "Neither Agree nor Disagree"},
                            {"value": 5, "text": "Agree"},
                            {"value": 6, "text": "Strongly Agree"},
                            {"value": 7, "text": "Completely Agree"}
                        ],
                        "rows": [
                            {"value": "1", "text": "The playlist supports me in getting to know the genre"},
                            {"value": "2", "text": "The playlist is useful in exploring the genre"},
                            {"value": "4", "text": "The songs in the playlist did not help me to explore the genre"},
                            {"value": "5", "text": "I feel supported by the playlist to explore the genre"}
                        ]
                    },
                    {
                        "type": "matrix",
                        "name": "satisfaction",
                        "title": "Please indicate to what extent you agree or disagree with each statement",
                        "isAllRowRequired": "true",
                        "columns": [
                            {"value": 1, "text": "Completely Disagree"},
                            {"value": 2, "text": "Strongly Disagree"},
                            {"value": 3, "text": "Disagree"},
                            {"value": 4, "text": "Neither Agree nor Disagree"},
                            {"value": 5, "text": "Agree"},
                            {"value": 6, "text": "Strongly Agree"},
                            {"value": 7, "text": "Completely Agree"}
                        ],
                        "rows": [
                            {"value": "1", "text": "I would use this genre exploration tool again."},
                            {"value": "2", "text": "I did not like the genre exploration tool"},
                            {"value": "3", "text": "I would recommend the genre exploration tool to others"},
                            {"value": "4", "text": "I enjoyed using the genre exploration tool"}
                        ]
                    }
                ]
                }],
            "completedHtml": "Redirecting to the next page..."
        }

        survey_config = {
            'title': 'Survey about your experience with the recommendations and interface',
            'description': 'Please fill in this survey about your experience with the recommendations and interface',
            'next_url': url_for("session2_bp.explore_genre")
        }

        return render_template('survey.html', survey=survey, surveydata=surveydata, survey_config=survey_config)

    if request.method == "POST":
        recommendation = RecommendationLog.query.filter_by(id=rec_id).first()
        recommendation.survey_response[:] = [
            SurveyResponse(user_id=session["userid"],
                           session_id=session["id"],
                           rec_id=rec_id,
                           item_id=item,
                           value=request.form[item]) for item in
            request.form]
        db.session.commit()
        return "done"


@session2_bp.route('/explore_genre')
def explore_genre():
    prev_playlist_session = UserPlaylistSession.query.filter_by(user_id=session["userid"],
                                                                ).order_by(UserPlaylistSession.session_num.desc()).first()

    rec_id = prev_playlist_session.rec_id
    weight = prev_playlist_session.weight

    recommendation_log = RecommendationLog.query.filter_by(id=rec_id).first()
    genre = recommendation_log.genre_name

    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    if user_condition:
        condition = user_condition.condition
        return render_template('explore_genre_vis.html',
                               condition=condition,
                               genre=genre,
                               weight=weight)

