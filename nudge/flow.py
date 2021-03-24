from flask import render_template, redirect, Blueprint, request, session, url_for
from recommendation import RecommendationLog
import re
import time
from recommendation import SurveyResponse
from database import db
from general import UserCondition
import random

nudge_bp = Blueprint('nudge_bp', __name__, template_folder='templates')


@nudge_bp.route('/')
def index():
    return render_template('main2.html')


@nudge_bp.route('/redirect_from_main2')
def redirect_from_main2():
    # assign study condition
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    if not user_condition:
        condition = random.randint(0, 3)

        condition_text = "explore, representative"

        if condition == 1:
            condition_text = "explore, mixed"
        if condition == 2:
            condition_text = "close, representative"
        if condition == 3:
            condition_text = "close, mixed"

        user_condition_new = UserCondition(user_id=session["userid"],
                                           timestamp=time.time(),
                                           condition=condition, default=condition_text)
        db.session.add(user_condition_new)
        db.session.commit()

    return redirect('select_genre2')


@nudge_bp.route('/select_genre2')
def select_genre2():
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    return render_template("select_genre2.html", condition=user_condition.condition)


@nudge_bp.route('/explore_genre2')
def explore_genre2():

    # infer the experimental condition
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    user_condition_num = user_condition.condition
    weight = 0

    if user_condition_num == 1 or user_condition_num == 3:
        weight = 0.5
    
    return render_template('explore_genre2.html',
                           genre=request.args.get('genre'),
                           weight=weight)


@nudge_bp.route('/last_step')
def last_step():
    return render_template("general_last_page.html")


@nudge_bp.route('/post_task_survey', methods=["GET", "POST"])
def post_task_survey():
    if request.method == "GET":
        responses = RecommendationLog.query.filter_by(id=session["rec_id"]).first().survey_response
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
            "pages": [{
                "questions": [{
                    "type": "matrix",
                    "name": "Help",
                    "title": "Below you can find some questions related to your experience with the interface and "
                             "the correctness of the algorithm that recommended the sessions to you."
                             "Please indicate to what extent you agree or disagree with each statement.",
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
                        {"value": "1", "text": "The playlist supports me in getting to know the new genre."},
                        {"value": "2", "text": "The playlist motivates me to delve deeper into the new genre."},
                        {"value": "3", "text": "The playlist is useful in exploring a new genre."}
                    ]
                }]
            }],
            "completedHtml": "Redirecting to the next page..."
        }

        survey_config = {
            'title': 'Survey about your experience with the recommendations and interface',
            'description': 'Please fill in this survey about your experience with the recommendations and interface',
            'next_url': url_for('nudge_bp.last_step')
        }

        return render_template('survey.html', survey=survey, surveydata=surveydata, survey_config=survey_config)

    if request.method == "POST":

        recommendation = RecommendationLog.query.filter_by(id=session["rec_id"]).first()

        recommendation.survey_response[:] = [
            SurveyResponse(user_id=session["userid"],
                           session_id=session["id"],
                           rec_id=session["rec_id"],
                           item_id=item,
                           value=request.form[item], stop_ts=time.time()) for item in
            request.form]
        db.session.commit()
        return "done"

