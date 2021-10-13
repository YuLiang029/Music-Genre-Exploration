from flask import render_template, Blueprint, session, jsonify, redirect, url_for, request
import pandas as pd
import time as time
import uuid
from recommendation import RecommendationLog
from database import db
from recommendation.recommendation import get_genre_recommendation_by_preference
from recommendation import RecTracks, SurveyResponse
from dbdw import RecStream, SelectedStream, ImgRatings, RecEvent, SelectedEvent, Events
import random
import re
from general import MsiResponse, UserCondition
import os
from flask_mail import Message
from mail import mail

dbdw_bp = Blueprint('dbdw_bp', __name__, template_folder='templates')
num_ssw, num_pop, num_jazz, num_harp = 20, 20, 20, 40
room_ssw, room_pop, room_jazz, room_harp = "room1", "room2", "room3", "room4"
timeslot1 = "19:35"
timeslot2 = "20:10"
l_timeslot = [timeslot1, timeslot2]


events = {
    "Singsongwriter": {"capacity": num_ssw, "event_room": room_ssw},
    "Pop musician": {"capacity": num_pop, "event_room": room_pop},
    "Jazz musician": {"capacity": num_jazz, "event_room": room_jazz},
    "Harpist": {"capacity": num_harp, "event_room": room_harp}
}


@dbdw_bp.route('/')
def index():
    return render_template("main.html")


@dbdw_bp.route('/inform_consent')
def inform_consent():
    return render_template("form_consent.html")


@dbdw_bp.route('/assign_condition')
def assign_condition():
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()
    selected_event = SelectedEvent.query.filter_by(user_id=session["userid"]).count()

    if selected_event >= 2:
        return redirect(url_for("dbdw_bp.selection_made_exception"))

    if not user_condition:
        # randomly assign a user to a condition
        condition = random.randint(0, 1)

        # 0: nudge for distant performance
        # 1: nudge for close performance
        default = "distant"
        if condition == 1:
            default = "close"

        user_condition_new = UserCondition(user_id=session["userid"],
                                           timestamp=time.time(),
                                           condition=condition, default=default)
        db.session.add(user_condition_new)
        db.session.commit()
    return redirect(url_for("spotify_basic_bp.msi_survey", redirect_path="dbdw_bp.event_explore"))


@dbdw_bp.route('/selection_made_exception')
def selection_made_exception():
    return render_template("error_selection_already_made.html")


@dbdw_bp.route('/event_explore')
def event_explore():
    user_condition = UserCondition.query.filter_by(user_id=session["userid"]).first()

    print(user_condition.condition)
    return render_template("explore_performance.html",
                           condition=user_condition.condition,
                           default=user_condition.default)


def get_track_recommendations():
    dbdw_data_path = os.path.join(
        os.path.join(os.path.dirname(dbdw_bp.root_path),
                     'dbdw'), "dbdw_music.csv")

    track_df = pd.read_csv(dbdw_data_path, delimiter=";")

    ts = time.time()
    session['rec_id'] = str(uuid.uuid4())

    recommendation_log = RecommendationLog(id=session['rec_id'],
                                           user_id=session["userid"],
                                           session_id=session['id'],
                                           start_ts=ts)

    db.session.add(recommendation_log)
    db.session.commit()

    recommendations = get_genre_recommendation_by_preference(track_df=track_df, by_preference=True)
    for index, row in recommendations.iterrows():
        rec_tracks = RecTracks(rec_id=session['rec_id'], track_id=row["id"], rank=index)
        db.session.add(rec_tracks)
        db.session.commit()

    track_df_new = track_df[['id', 'event', 'stream']]
    tracks = track_df_new.merge(recommendations.drop(columns=['event', 'stream']), on=['id'])
    return tracks


@dbdw_bp.route('/event_recommendation/<perform_type>')
def event_recommendation(perform_type):
    tracks = get_track_recommendations()

    if perform_type == "stream":
        # list of two streams
        l_stream = ['stream a', 'stream b']

        # calculate stream recommendation score, valence mean and energy mean
        dict_stream_score = {}
        dict_stream_valence = {}
        dict_stream_energy = {}

        for stream in l_stream:
            df_stream = tracks[tracks["stream"] == stream]
            dict_stream_score[stream] = df_stream.sum_rank.sum()/len(df_stream)
            dict_stream_valence[stream] = df_stream.valence.sum() / len(df_stream)
            dict_stream_energy[stream] = df_stream.energy.sum() / len(df_stream)

        sorted_dict_stream_score = {k: v for k, v in sorted(dict_stream_score.items(),
                                                            key=lambda item: item[1],
                                                            reverse=True)}

        l_stream_recs = []
        for stream in sorted_dict_stream_score:
            dict_stream = {}

            dict_stream["tracks"] = tracks[tracks["stream"] == stream].to_dict('records')
            dict_stream["rec_scores"] = sorted_dict_stream_score[stream]

            dict_stream["stream_valence"] = dict_stream_valence[stream]
            dict_stream["stream_energy"] = dict_stream_energy[stream]

            dict_stream["stream"] = stream

            l_stream_recs.append(dict_stream)

            db.session.add(RecStream(rec_id=session['rec_id'],
                                     stream_name=stream,
                                     rec_scores=dict_stream["rec_scores"],
                                     stream_valence=dict_stream["stream_valence"],
                                     stream_energy=dict_stream["stream_energy"],
                                     session_id=session['id'],
                                     user_id=session['userid'],
                                     timestamp=time.time()
                                     ))
        print(l_stream_recs)
        db.session.commit()
        return jsonify(l_stream_recs)

    elif perform_type == "performance":
        # code for event recommendation
        # calculate event recommendation score, valence mean and energy mean
        dict_event_score = {}
        dict_event_valence = {}
        dict_event_energy = {}

        l_event = ['Singsongwriter', 'Pop musician', 'Harpist', 'Jazz musician']
        for event in l_event:
            df_event = tracks[tracks["event"] == event]
            dict_event_score[event] = df_event.sum_rank.sum() / len(df_event)
            dict_event_valence[event] = df_event.valence.sum() / len(df_event)
            dict_event_energy[event] = df_event.energy.sum() / len(df_event)

        sorted_dict_event_score = {k: v for k, v in sorted(dict_event_score.items(),
                                                           key=lambda item: item[1],
                                                           reverse=True)}
        l_event_recs = []
        for event in sorted_dict_event_score:

            # dictionary for the event
            dict_event = {}

            # attach track attributes
            dict_event["tracks"] = tracks[tracks["event"] == event].to_dict('records')

            # attach recommendation score
            dict_event["rec_scores"] = sorted_dict_event_score[event]

            # attach feature attributes
            dict_event["event_valence"] = dict_event_valence[event]
            dict_event["event_energy"] = dict_event_energy[event]

            dict_event["event"] = event

            db.session.add(RecEvent(rec_id=session['rec_id'],
                                    event_id=event,
                                    rec_scores=dict_event["rec_scores"],
                                    event_valence=dict_event_valence[event],
                                    event_energy=dict_event_energy[event],
                                    session_id=session['id'],
                                    user_id=session['userid'],
                                    timestamp=time.time()
                                    ))
            l_event_recs.append(dict_event)

        db.session.commit()

        print(l_event_recs)
        return jsonify(l_event_recs)


@dbdw_bp.route('/register_event')
def register_event():
    for event in events:
        for timeslot in l_timeslot:
            event_obj = Events(event_name=event, event_timeslot=timeslot, event_room=events[event]["event_room"],
                               spots_available=events[event]["capacity"])
            db.session.add(event_obj)
            db.session.commit()
    return jsonify("done")


@dbdw_bp.route('/save_selected_stream')
def save_selected_stream():
    stream = request.args.get('stream')

    db.session.add(
        SelectedStream(rec_id=session['rec_id'],
                       stream_name=stream,
                       session_id=session['id'],
                       user_id=session['userid'],
                       timestamp=time.time()
                       ))
    db.session.commit()

    return redirect(url_for('dbdw_bp.post_task_survey'))


@dbdw_bp.route('/save_selected_event')
def save_selected_event():
    selected_events = request.args.getlist('event')
    event1 = selected_events[0]
    event2 = selected_events[1]

    event1_capacity = events[selected_events[0]]["capacity"]
    event2_capacity = events[selected_events[1]]["capacity"]

    dict_spots_option1 = {}
    dict_spots_option2 = {}

    # # check the number of registration of the selected events
    dict_spots_option1["remain_event1_t1"] = event1_capacity - SelectedEvent.query.filter_by(
        event_name=event1,
        event_timeslot=timeslot1).count()
    dict_spots_option1["remain_event2_t2"] = event2_capacity - SelectedEvent.query.filter_by(
        event_name=event2,
        event_timeslot=timeslot2).count()

    min_option1 = min(dict_spots_option1.values())
    sum_option1 = sum(dict_spots_option1.values())

    dict_spots_option2["remain_event2_t1"] = event2_capacity - SelectedEvent.query.filter_by(
        event_name=event2,
        event_timeslot=timeslot1).count()
    dict_spots_option2["remain_event1_t2"] = event1_capacity - SelectedEvent.query.filter_by(
        event_name=event1,
        event_timeslot=timeslot2).count()
    min_option2 = min(dict_spots_option2.values())
    sum_option2 = sum(dict_spots_option2.values())

    event1_occupied = SelectedEvent.query.filter_by(event_name=event1).all()
    event2_occupied = SelectedEvent.query.filter_by(event_name=event2).all()

    num_event1_occupied = 0
    for e1_occupied in event1_occupied:
        num_event1_occupied = num_event1_occupied + e1_occupied

    num_event2_occupied = 0
    for e2_occupied in event2_occupied:
        num_event2_occupied = num_event2_occupied + e2_occupied

    event1_spots_available = event1_capacity - num_event1_occupied
    event2_spots_available = event2_capacity - num_event2_occupied
    print(min_option1, min_option2, sum_option1, sum_option2, event1_spots_available, event2_spots_available)

    # check the number of people for the concert
    num_people = MsiResponse.query.filter_by(user_id=session["userid"],
                                             item_id="ticketnum").first().value

    minimal_aval_spots = 0

    if num_people != 1:
        minimal_aval_spots = 1

    # simple greedy algorithm for scheduling
    if min_option1 > minimal_aval_spots or min_option2 > minimal_aval_spots:
        if min_option1 < min_option2:
            # E2, E1
            save_events = [selected_events[1], selected_events[0]]
        elif min_option1 > min_option2:
            # E1, E2
            save_events = [selected_events[0], selected_events[1]]
        else:
            # if there is a tie
            if sum_option1 <= sum_option2:
                # E2, E1
                save_events = [selected_events[1], selected_events[0]]
            else:
                # E1, E2
                save_events = [selected_events[0], selected_events[1]]
        print(save_events)

        for i in range(len(save_events)):
            db.session.add(
                SelectedEvent(rec_id=session['rec_id'],
                              event_timeslot=l_timeslot[i],
                              event_name=save_events[i],
                              session_id=session['id'],
                              num_people=num_people,
                              user_id=session['userid'],
                              timestamp=time.time()
                              )
            )
            db.session.commit()
        return "done"
    else:
        if event1_spots_available <= minimal_aval_spots and event2_spots_available <= minimal_aval_spots:
            data = {'return_message': "both events are not available any more", 'num_people': num_people}
        else:
            if event1_spots_available <= minimal_aval_spots:
                data = {'return_message': "event 1 is not available", 'num_people': num_people}
            elif event2_spots_available <= minimal_aval_spots:
                data = {'return_message': "event 2 is not available", 'num_people': num_people}
            else:
                data = {'return_message': "this combination is not available anymore", 'num_people': num_people}
        return jsonify(data)


@dbdw_bp.route('/post_task_survey', methods=["GET", "POST"])
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
                    "name": "Eval",
                    "title": "Please indicate to what extent you agree or disagree with each statement.",
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
                        {"value": "1", "text": "The system motivates me to explore more out of my bubble."},
                        {"value": "2", "text": "I feel supported by the system to explore out of my bubble."},
                        {"value": "3", "text": "I feel the system is not helpful in exploring out of my bubble."},
                        {"value": "4", "text": "The performance that is more out of my bubble challenges "
                                               "me to explore a new music taste."},
                        {"value": "5", "text": "The visualization helped me "
                                               "in understanding my own musical tastes."},
                        {"value": "6", "text": "The visualization helped me in "
                                               "understanding the song characteristics of the different performances."},
                        {"value": "7", "text": "The visualization helped me in choosing which two "
                                               "performances to go to."}

                    ]
                }]
            }],
            "completedHtml": "Redirecting to the next page..."
        }

        survey_config = {
            'title': 'Survey about your experience with the recommendations and interface',
            'description': 'Please fill in this survey about your experience with the recommendations and interface ',
            'next_url': url_for('dbdw_bp.registration_overview')
        }

        return render_template('survey.html', survey=survey, surveydata=surveydata, survey_config=survey_config)

    if request.method == "POST":

        recommendation = RecommendationLog.query.filter_by(id=session["rec_id"]).first()

        recommendation.survey_response[:] = [
            SurveyResponse(user_id=session["userid"],
                           session_id=session["id"],
                           rec_id=session['rec_id'],
                           item_id=item,
                           value=request.form[item], stop_ts=time.time()) for item in
            request.form]
        db.session.commit()
        return "done"


@dbdw_bp.route('/final_step')
def final_step():

    email_address = MsiResponse.query.filter_by(user_id=session["userid"],
                                                item_id="email").first().value

    selected_stream = SelectedStream.query.filter_by(rec_id=session["rec_id"]).first().stream_name
    selected_stream_strip = selected_stream.replace("stream", "").strip()
    print(selected_stream_strip)

    return render_template("last_page.html", email_address=email_address, selected_stream=selected_stream_strip)


@dbdw_bp.route('/registration_overview')
def registration_overview():
    event1 = SelectedEvent.query.filter_by(rec_id=session["rec_id"], event_timeslot=timeslot1).first().event_name
    event2 = SelectedEvent.query.filter_by(rec_id=session["rec_id"], event_timeslot=timeslot2).first().event_name

    return render_template("last_page_2021.html",
                           timeslot1=timeslot1,
                           timeslot2=timeslot2,
                           event1=event1,
                           event2=event2)


@dbdw_bp.route('/send_email')
def send_email():
    email_address = MsiResponse.query.filter_by(user_id=session["userid"],
                                                item_id="email").first().value
    msg = Message(sender=os.environ.get('MAIL_USERNAME'), recipients=[email_address])
    msg.subject = "Data Week Nederland Cultural Night Registration"

    selected_event = SelectedEvent.query.filter_by(rec_id=session["rec_id"])
    event1 = selected_event[0].event_name
    event2 = selected_event[1].event_name

    msg.html = "<h3>Thanks for registering for the concert!</h3>" \
               "<p>You have made a registration for two people. Your selected performances are:</p>" \
               "<p>1. " + event1 + " at " + timeslot1 + ", 26 Oct</p><p>2. " \
               + event2 + " at " + timeslot2 + ", 26 Oct</p> " \
               "<div> <img src=\"{{ url_for('static', filename='imgs/JADS_logo_RGB.png') }}\" alt=\"Jheronimus Academy of Data Science\"/ " \
                                                           "style=\"width:300px\"></div>" \
               "<div><img src=\"{{ url_for('static', filename='imgs/logo_tue.svg') }}\" " \
                                                           "alt=\"Eindhoven University of Technology\"/ " \
                                                           "style=\"width:300px\"></div>"

    mail.send(msg)
    return "done"


@dbdw_bp.route('/rating')
def rating():
    return render_template('rating.html')


@dbdw_bp.route('/get_items_to_rate')
def get_items_to_rate():

    l_images = []
    l_image_id = ["0_centroid", "0_outlier",
                  "1_centroid", "1_outlier",
                  "2_centroid", "2_outlier", "3_centroid", "3_outlier"]

    for image_id in l_image_id:
        l_images.append(url_for('static', filename='paintings/' + image_id + ".jpg"))
    return jsonify(l_images)


@dbdw_bp.route('/submit_ratings', methods=["POST"])
def submit_ratings():
    user_id = session["userid"]
    session_id = session["id"]
    ts = time.time()

    if request.method == 'POST':
        try:
            dict_data = dict(request.form)

            for key in dict_data:
                score = dict_data[key]
                print(key)
                print(score)
                db.session.add(ImgRatings(user_id=user_id, session_id=session_id, ts=ts, img_id=key, rating=score))
            db.session.commit()
            return "success"
        except Exception as e:
            print(e)
            return "error"
