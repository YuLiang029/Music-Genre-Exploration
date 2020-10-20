# from flask import render_template, redirect, url_for, session, request, jsonify
# from flask import Blueprint
# import json
# from database import db
# from nov_music import Event, EventArtists
# from general import Artist, Track, ArtistTracks, User
# from general.basic import spotify, scrape_artist_tracks
# from recommendation.recommendation import get_genre_recommendation_by_preference
# import numpy as np
# import os
# import pandas as pd
# import time
# import uuid
# from recommendation import RecommendationLog, RecTracks
#
# pd.set_option('display.max_columns', None)
# nov_bp = Blueprint('nov_bp', __name__, template_folder='templates')
#
#
# @nov_bp.route('/')
# def index():
#     return render_template('main.html')
#
#
# @nov_bp.route('/test_url')
# def test_url():
#     return render_template("test.html")
#
#
# @nov_bp.route('/load_event')
# def load_event():
#     path = '/Users/yuliang/Desktop/text_for_novmusic/event_test.json'
#
#     with open(path) as json_file:
#         events = json.load(json_file)['events']
#
#     for event in events:
#         event_obj = Event(name=event["name"], info=event["info"], url=event["url"], artists=event["artists"])
#         db.session.add(event_obj)
#
#         for artist in event['spotify_artists']:
#             artist_id = artist['artist_id']
#             artist = Artist.query.filter_by(id=artist_id).first()
#
#             if artist:
#                 new_event_artist = EventArtists(event_id=event_obj.id,
#                                                 artist_id=artist.id,
#                                                 artist=artist)
#                 db.session.add(new_event_artist)
#                 db.session.commit()
#
#             else:
#                 url = '/v1/artists/' + artist_id
#                 artist_request = spotify.request(url)
#
#                 if artist_request.status != 200:
#                     return "top_artists_request status: " + str(artist_request.status), 400
#                 else:
#                     artist_result = artist_request.data
#                     new_artist_obj = Artist(
#                         id=artist_result["id"],
#                         followers=artist_result["followers"]["total"],
#                         genres=",".join(artist_result["genres"]),
#                         image_middle=None if len(artist_result["images"]) == 0 else artist_result["images"][1]["url"],
#                         name=artist_result["name"],
#                         popularity=artist_result["popularity"],
#                         external_urls=artist_result["external_urls"]["spotify"],
#                         href=artist_result["href"],
#                         uri=artist_result["uri"]
#
#                     )
#
#                     new_event_artist = EventArtists(event_id=event_obj.id,
#                                                     artist_id=artist_result["id"],
#                                                     artist=new_artist_obj)
#                     db.session.add(new_event_artist)
#                     db.session.commit()
#
#     return render_template("test.html")
#
#
# @nov_bp.route('/scrape_event_artist_tracks')
# def scrape_event_artist_tracks():
#     event_artists = db.session.query(EventArtists).group_by(EventArtists.artist_id).all()
#     for artist in event_artists:
#         print(artist.artist_id)
#         scrape_artist_tracks(artist.artist_id)
#     return render_template("test.html")
#
#
# @nov_bp.route('/generate_event_recommendations')
# def generate_event_recommendations():
#     # event_tracks = db.session.query(EventArtists,
#     #                                 ArtistTracks,
#     #                                 Track).filter().join(
#     #     ArtistTracks, EventArtists.artist_id == ArtistTracks.artist_id).join(
#     #     Track, ArtistTracks.track_id == Track.id).all()
#
#     track_df = pd.read_sql(db.session.query(EventArtists,
#                                             ArtistTracks,
#                                             Track).filter().join(
#         ArtistTracks, EventArtists.artist_id == ArtistTracks.artist_id).join(
#         Track, ArtistTracks.track_id == Track.id).statement, db.session.bind)
#
#     print(track_df)
#
#     ts = time.time()
#     session['rec_id'] = str(uuid.uuid4())
#
#     recommendation_log = RecommendationLog(id=session['rec_id'],
#                                            user_id=session["userid"],
#                                            session_id=session['id'],
#                                            start_ts=ts)
#
#     db.session.add(recommendation_log)
#     db.session.commit()
#
#     recommendations = get_genre_recommendation_by_preference(track_df=track_df, by_preference=False)
#
#     for index, row in recommendations.iterrows():
#         rec_tracks = RecTracks(rec_id=session['rec_id'], track_id=row["id"], rank=index)
#         db.session.add(rec_tracks)
#         db.session.commit()
#
#     event_score = {}
#     for event_id in range(1, 11):
#         l_tracks = track_df[track_df["event_id"] == event_id].id.tolist()
#         event_recs = recommendations[recommendations["id"].isin(l_tracks)]
#         event_score[event_id] = event_recs.sum_rank.sum()/len(event_recs)
#
#     print(event_score)
#
#     event_df = pd.read_sql(db.session.query(Event).filter().statement, db.session.bind)
#
#     events = event_df.to_dict('records')
#     return jsonify(events)
#
