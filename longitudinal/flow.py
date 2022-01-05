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
session_num = 2


@longitudinal_bp.route('/')
def index():
    return render_template('main.html')


@longitudinal_bp.route('/redirect_from_index')
def redirect_from_index():
    """
    Check if subject_id exists
    """
    if request.args.get("subject_id"):
        session["subject_id"] = request.args.get("subject_id")
        print(session["subject_id"])

        return redirect(url_for("longitudinal_bp.session_register"))

    return redirect(url_for("longitudinal_bp.error_page"))


@longitudinal_bp.route('/session_register')
def session_register():
    """
    Session1 Redirect for informed consent
    """
    # Session1 Redirect
    if session_num == 1:
        return redirect(url_for("longitudinal_bp.inform_consent"))

    # Session2, Session3, and Session4 Redirect
    # First check if user_condition exists already
    user_condition = UserCondition.query.filter_by(user_id=session["subject_id"]).first()
    if not user_condition:
        return redirect(url_for("longitudinal_bp.error_page"))

    """
        Session2, Session3, Session4 Redirect
    """
    if session_num >= 2:
        return redirect(url_for('spotify_basic_bp.login',
                                next_url='longitudinal_bp.pre_survey'))


@longitudinal_bp.route('/inform_consent')
def inform_consent():
    return render_template('informed_consent.html')


@longitudinal_bp.route('/register_informed_consent')
def register_informed_consent():
    if request.args.get("consent") == "False":
        return redirect(url_for("longitudinal_bp.disagree_informed_consent"))

    if 'subject_id' in session:
        session["share"] = request.args.get("share")
        return redirect(url_for('spotify_basic_bp.login',
                                next_url='longitudinal_bp.first_session'))

    return redirect(url_for("longitudinal_bp.error_page"))


@longitudinal_bp.route('/first_session')
def first_session():
    """
    Session1
    """
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


@longitudinal_bp.route('/pre_survey', methods=["GET", "POST"])
def pre_survey():
    rec_id = UserPlaylistSession.query.filter_by(user_id=session["userid"]).first().rec_id
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
            'next_url': url_for("longitudinal_bp.explore_genre")
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


@longitudinal_bp.route('/select_genre')
def select_genre():
    return render_template("select_genre.html")


@longitudinal_bp.route('/explore_genre')
def explore_genre():
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    if not user_condition:
        return redirect(url_for(error_page))

    user_condition_num = user_condition.condition

    if session_num == 1:
        # infer the experimental condition
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
        rec_id=rec_id,
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


@longitudinal_bp.route('/error_page')
def error_page():
    return render_template("Error_non_prolificid.html")
