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
    return render_template('main.html')


@nudge_bp.route('/inform_consent')
def inform_consent():
    # for getting subject id
    # if request.args.get("subject_id"):
    #     session["subject_id"] = request.args.get("subject_id")
    #     print(session["subject_id"])
    #     return render_template('informed_consent.html')
    #
    # return redirect(url_for("nudge_bp.error_page"))
    return render_template('informed_consent.html')


@nudge_bp.route('/register')
def register():
    if request.args.get("consent") == "False":
        return redirect(url_for("nudge_bp.disagree_informed_consent"))

    if 'subject_id' in session:
        session["share"] = request.args.get("share")
        return redirect(url_for('spotify_basic_bp.login', next_url='nudge_bp.redirect_from_main'))
    else:
        return redirect(url_for("nudge_bp.error_page"))


@nudge_bp.route('/register_without_subject_id')
def register_without_subject_id():
    session["session_num"] = 1
    if request.args.get("consent") == "False":
        return redirect(url_for("nudge_bp.disagree_informed_consent"))

    session["share"] = request.args.get("share")
    return redirect(url_for('spotify_basic_bp.login', next_url='nudge_bp.redirect_from_main'))


@nudge_bp.route('/redirect_from_main')
def redirect_from_main():
    # assign study condition
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    if not user_condition:
        # condition = random.randint(0, 5)
        # set condition to explore and representative
        condition_text = "explore, representative"
        condition = 0

        if condition == 1:
            condition_text = "explore, mixed"
        if condition == 2:
            condition_text = "explore, personalized"
        if condition == 3:
            condition_text = "close, representative"
        if condition == 4:
            condition_text = "close, mixed"
        if condition == 5:
            condition_text = "close, personalized"

        user_condition_new = UserCondition(user_id=session["userid"],
                                           timestamp=time.time(),
                                           condition=condition, default=condition_text)
        db.session.add(user_condition_new)
        db.session.commit()

    return redirect(url_for("spotify_basic_bp.msi_survey", redirect_path="nudge_bp.select_genre"))
    # return redirect(url_for("nudge_bp.select_genre"))


@nudge_bp.route('/select_genre')
def select_genre():
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    return render_template("select_genre.html", condition=user_condition.condition)


@nudge_bp.route('/explore_genre')
def explore_genre():
    # infer the experimental condition
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    user_condition_num = user_condition.condition
    weight = 0

    if user_condition_num == 1 or user_condition_num == 4:
        weight = 0.5
    if user_condition_num == 2 or user_condition_num == 5:
        weight = 1

    return render_template('explore_genre.html',
                           genre=request.args.get('genre'),
                           weight=weight)


@nudge_bp.route('/last_step')
def last_step():
    # return redirect("https://app.prolific.co/submissions/complete?cc=47904236")
    return render_template("general_last_page.html")


@nudge_bp.route('/post_task_survey', methods=["GET", "POST"])
def post_task_survey():
    if request.method == "GET":
        recommendation_log = RecommendationLog.query.filter_by(id=session["rec_id"]).first()
        responses = recommendation_log.survey_response
        recommendation_log.stop_ts = time.time()
        db.session.commit()

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
                # {"questions": [{
                #     "type": "matrix",
                #     "name": "repr",
                #     "title": "Please indicate to what extent you agree or disagree with each statement about "
                #              "the playlist you just created",
                #     "isAllRowRequired": "true",
                #     "columns": [
                #         {"value": 1, "text": "Completely Disagree"},
                #         {"value": 2, "text": "Strongly Disagree"},
                #         {"value": 3, "text": "Disagree"},
                #         {"value": 4, "text": "Neither Agree nor Disagree"},
                #         {"value": 5, "text": "Agree"},
                #         {"value": 6, "text": "Strongly Agree"},
                #         {"value": 7, "text": "Completely Agree"}
                #     ],
                #     "rows": [
                #         {"value": "1", "text": "The playlist matches the style of the genre"},
                #         {"value": "2", "text": "The playlist contains songs I would expect from the genre"},
                #         {"value": "3", "text": "The songs of the playlist are less typical of the genre"},
                #         {"value": "4", "text": "The playlist represents the mainstream tastes of the genre"},
                #     ]
                # }, {
                #     "type": "matrix",
                #     "name": "pers",
                #     "title": "Please indicate to what extent you agree or disagree with each statement "
                #              "about the playlist you just created",
                #     "isAllRowRequired": "true",
                #     "columns": [
                #         {"value": 1, "text": "Completely Disagree"},
                #         {"value": 2, "text": "Strongly Disagree"},
                #         {"value": 3, "text": "Disagree"},
                #         {"value": 4, "text": "Neither Agree nor Disagree"},
                #         {"value": 5, "text": "Agree"},
                #         {"value": 6, "text": "Strongly Agree"},
                #         {"value": 7, "text": "Completely Agree"}
                #     ],
                #     "rows": [
                #         {"value": "1", "text": "The playlist is personalized to my music tastes"},
                #         {"value": "2", "text": "The playlist has songs with styles I like to listen to"},
                #         {"value": "3", "text": "I find the songs from the playlist appealing"},
                #         {"value": "4", "text": "I would listen to the playlist again"},
                #     ]
                # }]},
                # {"questions": [{
                #     "type": "matrix",
                #     "name": "ctrl",
                #     "title": "Please indicate to what extent you agree or disagree with each statement.",
                #     "isAllRowRequired": "true",
                #     "columns": [
                #         {"value": 1, "text": "Completely Disagree"},
                #         {"value": 2, "text": "Strongly Disagree"},
                #         {"value": 3, "text": "Disagree"},
                #         {"value": 4, "text": "Neither Agree nor Disagree"},
                #         {"value": 5, "text": "Agree"},
                #         {"value": 6, "text": "Strongly Agree"},
                #         {"value": 7, "text": "Completely Agree"}
                #     ],
                #     "rows": [
                #         {"value": "1", "text": "I felt in control of modifying the recommendations"},
                #         {"value": "2", "text": "I felt I couldn't really tell the system what I wanted in my playlist"},
                #         {"value": "3", "text": "I found it easy to modify the recommendations in the recommender"},
                #         {"value": "4", "text": "I was able to clearly specify my preferences"},
                #
                #     ]
                # }, {
                #     "type": "matrix",
                #     "name": "und",
                #     "title": "Please indicate to what extent you agree or disagree with each statement.",
                #     "isAllRowRequired": "true",
                #     "columns": [
                #         {"value": 1, "text": "Completely Disagree"},
                #         {"value": 2, "text": "Strongly Disagree"},
                #         {"value": 3, "text": "Disagree"},
                #         {"value": 4, "text": "Neither Agree nor Disagree"},
                #         {"value": 5, "text": "Agree"},
                #         {"value": 6, "text": "Strongly Agree"},
                #         {"value": 7, "text": "Completely Agree"}
                #     ],
                #     "rows": [
                #         {"value": "1", "text": "I understand how the recommended songs relate to my musical taste"},
                #         {"value": "2", "text": "It is easy to grasp why I received these recommended songs"},
                #         {"value": "3", "text": "The recommendation process was clear to me"},
                #         {"value": "4", "text": "I understand why the songs were recommended to me"},
                #         {"value": "5", "text": "It is important that you pay attention to this study. "
                #                                "Please tick 'Completely Disagree'"}
                #     ]
                # }]},
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
                            # {"value": "3", "text": "The playlist motivates me to delve more into the genre"},
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
            'next_url': url_for('nudge_bp.last_step')
        }

        return render_template('survey.html', survey=survey, surveydata=surveydata, survey_config=survey_config)

    if request.method == "POST":
        recommendation = RecommendationLog.query.filter_by(id=session["rec_id"]).first()
        stop_ts = time.time()
        recommendation.survey_response[:] = [
            SurveyResponse(user_id=session["userid"],
                           session_id=session["id"],
                           rec_id=session["rec_id"],
                           item_id=item,
                           value=request.form[item], stop_ts=stop_ts) for item in
            request.form]
        db.session.commit()
        return "done"


@nudge_bp.route('/error_page')
def error_page():
    return render_template("Error_non_prolificid.html")


@nudge_bp.route('/disagree_informed_consent')
def disagree_informed_consent():
    return render_template("Error_inform_consent.html")