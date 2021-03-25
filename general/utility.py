from general import Track
from basic import spotify_basic_bp
import pandas as pd
from database import db
from worker import conn
from rq import Queue


q = Queue(connection=conn)


# @spotify_basic_bp.route('/run_background_process')
# def run_background_process():


@spotify_basic_bp.route('/import_tracks_from_csv')
def import_tracks_from_csv():
    l_genre = ["avant-garde", "blues", "christmas",
               "classical", "country", "country",
               "electronic", "folk", "jazz",
               "latin", "new-age", "rap", "reggae", "rnb"]

    for genre in l_genre[:1]:

        df = pd.read_csv("genre_baseline/" + genre + ".csv", sep=";")

        for index, row in df.iterrows():
            track = Track.query.filter_by(id=row.id).first()
            if track:
                pass
            else:
                new_track_obj = Track(
                    id=row.id, trackname=row.trackname, popularity=row.popularity, preview_url=row.preview_url,
                    track_number=row.track_number, firstartist=row.firstartist, imageurl=row.imageurl,
                    spotifyurl=row.spotifyurl, acousticness=row.acousticness, danceability=row.danceability,
                    duration_ms=row.duration_ms, energy=row.energy, instrumentalness=row.instrumentalness,
                    key=row.key, liveness=row.liveness, loudness=row.loudness,
                    speechiness=row.speechiness, tempo=row.tempo, time_signature=row.time_signature,
                    valence=row.valence
                )
                if index % 100 == 0:
                    print(index)
                db.session.add(new_track_obj)
            db.session.commit()
