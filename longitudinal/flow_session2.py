from flask import render_template, redirect, Blueprint, request, session, url_for
import time
from database import db
from general import UserCondition
import random
from longitudinal import UserPlaylistSession, PostSurvey
from recommendation import SurveyResponse, RecommendationLog
import re

"""
Blueprint for session 2
"""

session2_bp = Blueprint('session2_bp', __name__, template_folder='templates')


@session2_bp.route('/')
def index():
    # session["session_num"] = 2
    # session["session_num"] = 3
    session["session_num"] = 4
    return render_template('main2.html')


@session2_bp.route('/session_login')
def session_login():
    if request.args.get("PROLIFIC_PID"):
        session["subject_id"] = request.args.get("PROLIFIC_PID")
        return redirect(url_for("session2_bp.session_instruction"))

    return redirect(url_for("long_bp.error_page"))


@session2_bp.route('/session_instruction')
def session_instruction():
    return render_template("session_instruction.html")


@session2_bp.route('/session_register')
def session_register():
    if session.get('subject_id'):
        # Check if the playlist has already been generated
        user_playlist_session = UserPlaylistSession.query.filter_by(
            user_id=session["subject_id"],
            session_num=session["session_num"]).first()

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
                        "name": "pers",
                        "title": "Please indicate to what extent you agree or disagree with each statement "
                                 "about the playlist from the last session",
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
                            {"value": "1", "text": "The playlist is personalized to my music tastes"},
                            {"value": "2", "text": "The playlist has songs with styles I like to listen to"},
                            {"value": "3", "text": "I find the songs from the playlist to fit my preferences"},
                        ]
                    },
                    {
                        "type": "matrix",
                        "name": "help",
                        "title": "Please indicate to what extent you agree or disagree with each statement "
                                 "about the playlist from the last session",
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
                            {"value": "5", "text": "Please tick 'Neither Agree nor Disagree' "
                                                   "to show that you pay attention"},
                            {"value": "3", "text": "The songs in the playlist did not help me to explore the genre"}
                        ]
                    },
                    {
                        "type": "matrix",
                        "name": "satisfaction",
                        "title": "Please indicate to what extent you agree or disagree with each statement "
                                 "about the playlist from the last session",
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
                            {"value": "1", "text": "I enjoyed listening to the playlist"},
                            {"value": "2", "text": "I would listen to the playlist again "},
                            {"value": "3", "text": "I did not like the playlist"},
                            {"value": "4", "text": "I find the songs from the playlist appealing"}
                        ]
                    }
                ]
                },
                {
                    "elements": [
                        {
                            "type": "radiogroup",
                            "name": "q1",
                            "title": "How many times did you listen to (part of) the playlist in the last week?",
                            "isRequired": "true",
                            "colCount": 4,
                            "choices": [
                                "0-1 times",
                                "2-3 times",
                                "4 times or more",
                            ]
                        }
                        ,
                        {
                            "type": "radiogroup",
                            "name": "q2",
                            "title": "Did you use the playlist to find new artists or songs of the selected genre?",
                            "isRequired": "true",
                            "colCount": 4,
                            "choices": [
                                "Yes",
                                "No"
                            ]
                        },
                        {
                            "type": "checkbox",
                            "name": "q3",
                            "isRequired": "true",
                            "title": "How did you use the playlist to find other artists "
                                     "or songs of the selected genre?",
                            "visibleIf": "{q2}='Yes'",
                            "choices": [
                                "Through related artists",
                                "Through songs of the same album",
                                "Through Spotify recommendations based on what's in the playlist",
                                "By going to song radio",
                                "Other"
                            ]

                        },
                        {
                            "type": "text",
                            "name": "q4",
                            "isRequired": "true",
                            "title": "If other, please specify how did "
                                     "you use the playlist to find other artists or songs of the selected genre",
                            "visibleIf": "{q2}='Yes' and {q3} contains 'Other'"
                        },
                        {
                            "type": "radiogroup",
                            "name": "q5",
                            "title": "Did you favor ❤️ some songs from the playlist?",
                            "isRequired": "true",
                            "colCount": 4,
                            "choices": [
                                "No",
                                "Yes, one song",
                                "Yes, more than one song"
                            ]
                        }, {
                            "type": "radiogroup",
                            "name": "q6",
                            "title": "Did you delete some songs from the playlist?",
                            "isRequired": "true",
                            "colCount": 4,
                            "choices": [
                                "No",
                                "Yes, one song",
                                "Yes, more than one song"
                            ]
                        }
                    ]
                },
            ],
            "completedHtml": "Redirecting to the next page..."
        }

        survey_config = {
            'title': 'Your experience with the playlist from the last session',
            'description': 'Please fill in this survey about your experience with the playlist from the last session',
            'next_url': url_for("session2_bp.explore_genre_history")
        }

        return render_template('survey.html', survey=survey, surveydata=surveydata, survey_config=survey_config)

    if request.method == "POST":
        recommendation = RecommendationLog.query.filter_by(id=rec_id).first()
        recommendation.survey_response[:] = [
            SurveyResponse(user_id=session["userid"],
                           session_id=session["id"],
                           rec_id=rec_id,
                           item_id=item,
                           value=request.form[item],
                           stop_ts=time.time()) for item in
            request.form]
        db.session.commit()
        return "done"


@session2_bp.route('/explore_genre_history')
def explore_genre_history():
    # Check if the playlist has already been generated
    user_playlist_session = UserPlaylistSession.query.filter_by(
        user_id=session["subject_id"],
        session_num=session["session_num"]).first()

    if not user_playlist_session:
        prev_playlist_session = UserPlaylistSession.query.filter_by(
            user_id=session["userid"],
        ).order_by(UserPlaylistSession.session_num.desc()).all()

        # retrieve the previous playlist weight and the corresponding genre
        l_rec_id = []
        l_weight = []

        for playlist_session in prev_playlist_session:
            dict_tmp = {"Session": "Session " + str(playlist_session.session_num), "weight": playlist_session.weight}
            if dict_tmp not in l_weight:
                l_weight.append(dict_tmp)
                l_rec_id.append(playlist_session.rec_id)

        genre = RecommendationLog.query.filter_by(id=l_rec_id[0]).first().genre_name
        user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
        print(l_weight)

        if user_condition:
            condition = user_condition.condition
            track_history = False
            session_participated = len(l_weight)

            if condition == 0 or condition == 1:
                if len(l_weight) > 1:
                    track_history = True

            return render_template('explore_genre_vis.html',
                                   condition=condition,
                                   l_weight=l_weight,
                                   session_participated=session_participated,
                                   track_history=track_history,
                                   genre=genre,
                                   weight=l_weight[0]["weight"])

    return redirect(url_for("long_bp.error_repeat_answer"))


@session2_bp.route('/explore_genre')
def explore_genre():
    prev_playlist_session = UserPlaylistSession.query.filter_by(
        user_id=session["userid"],
    ).order_by(UserPlaylistSession.session_num.desc()).first()

    # retrieve the previous playlist weight and the corresponding genre
    prev_rec_id = prev_playlist_session.rec_id
    prev_weight = prev_playlist_session.weight
    genre = RecommendationLog.query.filter_by(id=prev_rec_id).first().genre_name

    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    if user_condition:
        condition = user_condition.condition
        return render_template('explore_genre_vis.html',
                               condition=condition,
                               genre=genre,
                               weight=prev_weight)


@session2_bp.route('/post_survey', methods=["GET", "POST"])
def post_survey():
    if request.method == "GET":
        surveydata = {}

        survey = {
            "showProgressBar": "top",
            "pages": [
                {"questions": [
                    {
                        "type": "matrix",
                        "name": "ctrl",
                        "title": "Please indicate to what extent you agree or disagree with each statement "
                                 "about your experience with the genre exploration tool",
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
                            {"value": "1", "text": "I felt in control of modifying the recommendations"},
                            {"value": "2", "text": "I felt I couldn’t really tell the system "
                                                   "what I wanted in my playlist"},
                            {"value": "3", "text": "I found it easy to modify the recommendations in the recommender"},
                            {"value": "4", "text": "I was able to clearly specify my preferences"}
                        ]
                    },
                    {
                        "type": "matrix",
                        "name": "help2",
                        "title": "Please indicate to what extent you agree or disagree with each statement "
                                 "about your experience with the genre exploration tool",
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
                            {"value": "1", "text": "The genre exploration app supports me in getting to know the genre"},
                            {"value": "2", "text": "The genre exploration app is useful in exploring the genre"},
                            {"value": "3", "text": "The genre exploration app did not help me to explore the genre"},
                            {"value": "4", "text": "The genre exploration app motivates me to delve more into the genre"},
                        ]
                    },
                    {
                        "type": "matrix",
                        "name": "useful",
                        "title": "Please indicate to what extent you agree or disagree with each statement "
                                 "about your experience with the genre exploration tool",
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
                            {"value": "1", "text": "The genre exploration app has no real benefit for me"},
                            {"value": "2", "text": "I would recommend the genre exploration app to others"},
                            {"value": "3", "text": "The genre exploration app is useful"},
                            {"value": "4", "text": "I would use the system again to explore other music genres"}
                        ]
                    }
                ]
                },
                {
                    "elements": [
                        {
                            "type": "text",
                            "name": "like",
                            "title": "What do you like about the music genre exploration tool?",
                        },

                        {
                            "type": "text",
                            "name": "dislike",
                            "title": "What do you dislike about the music genre exploration tool?",
                        },

                        {
                            "type": "text",
                            "name": "new",
                            "title": "What other features or improvements would you "
                                     "suggest for the music genre exploration tool?"
                        },
                    ]
                },
            ],
            "completedHtml": "Redirecting to the next page..."
        }

        survey_config = {
            'title': 'Your experience with the genre exploration tool',
            'description': 'We would like to know a bit more about '
                           'your experience with the music genre exploration tool',
            'next_url': url_for("long_bp.last_step_s4")
        }

        return render_template('survey.html', survey=survey, surveydata=surveydata, survey_config=survey_config)

    if request.method == "POST":
        responses = []
        stop_ts = time.time()
        responses[:] = [
            PostSurvey(user_id=session["userid"],
                       item_id=item,
                       value=request.form[item],
                       stop_ts=stop_ts) for item in
            request.form]
        db.session.add_all(responses)
        db.session.commit()
        return "done"

