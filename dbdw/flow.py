from flask import render_template, Blueprint, session, jsonify, redirect
import pandas as pd
import time as time
import uuid
from recommendation import RecommendationLog
from database import db
from recommendation.recommendation import get_genre_recommendation_by_preference
from recommendation import RecTracks


dbdw_bp = Blueprint('dbdw_bp', __name__, template_folder='templates')


@dbdw_bp.route('/')
def index():
    return render_template('main.html')


@dbdw_bp.route('/test_url')
def test_url():
    return render_template("form_consent.html")


@dbdw_bp.route('/event_explore')
def event_explore():
    control = 1
    vis = 1
    return render_template("explore_event.html", control=control, vis=vis)


@dbdw_bp.route('/event_recommendation')
def event_recommendation():
    track_df = pd.read_csv("test.csv")

    ts = time.time()
    session['rec_id'] = str(uuid.uuid4())

    recommendation_log = RecommendationLog(id=session['rec_id'],
                                           user_id=session["userid"],
                                           session_id=session['id'],
                                           start_ts=ts)

    db.session.add(recommendation_log)
    db.session.commit()

    recommendations = get_genre_recommendation_by_preference(track_df=track_df, by_preference=False)

    for index, row in recommendations.iterrows():
        rec_tracks = RecTracks(rec_id=session['rec_id'], track_id=row["id"], rank=index)
        db.session.add(rec_tracks)
        db.session.commit()

    tracks = recommendations.merge(track_df[['id', 'event']], on=['id'])
    return jsonify(tracks.to_dict('records'))



