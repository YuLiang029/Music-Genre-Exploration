from general import Track
import pandas as pd
from database import db
from worker import conn
from rq import Queue
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import Spotify
import json
from flask import Blueprint
from Utility import GenreArtist
from flask import render_template

utility_bp = Blueprint('utility_bp', __name__)

q = Queue(connection=conn)


def client_credentials_manager(client_id, client_secret):
    """
    set up client credential manager
    :return: Spotify client credential manager
    """
    ccm = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = Spotify(client_credentials_manager=ccm)
    sp.trace = False
    return sp


try:
    keys = json.load(open('keys.json', 'r'))
except Exception as e:
    print(e)


@utility_bp.route('/run_background')
def run_background():
    q.enqueue(scrape_genre_artist)
    return render_template("test.html")


# handler for scraping the first-level genre-artist from Spotify
@utility_bp.route('/scrape_genre_artist')
def scrape_genre_artist():
    sp = client_credentials_manager(keys["CLIENT_ID"], keys["CLIENT_SECRET_ID"])
    l_genre_scrape = ["pop-rock"]

    for genre in l_genre_scrape:
        all_music_artist = pd.read_csv("original_genre_artist_from_all_music/" + genre + ".csv",
                                       sep="\n",
                                       names=["artist_name"])

        artist_list = all_music_artist.artist_name.tolist()
        for artist in artist_list:
            try:
                x = sp.search(q=artist, type='artist')['artists']['items'][0]

                artist_existed = GenreArtist.query.filter_by(artist_id=x['id'], genre_allmusic=genre).first()
                if artist_existed:
                    pass
                else:
                    new_artist_obj = GenreArtist(
                        artist_id=x['id'],
                        followers=x["followers"]["total"],
                        genres=",".join(x["genres"]),
                        image_middle=None if len(x["images"]) == 0 else x["images"][1]["url"],
                        name=x['name'],
                        popularity=x["popularity"],
                        external_urls=x["external_urls"]["spotify"],
                        href=x["href"],
                        uri=x["uri"],
                        level=1,
                        genre_allmusic=genre
                    )
                    db.session.add(new_artist_obj)
                db.session.commit()
            except Exception as e:
                print(e)
    sp.__del__()
    return "success"


# handler for scraping the next-level genre-artist
@utility_bp.route('/scrape_genre_artist_next_level/<current_level>')
def scrape_genre_artist_next_level(current_level):
    sp = client_credentials_manager(keys["CLIENT_ID"], keys["CLIENT_SECRET_ID"])
    genre_artists = GenreArtist.query.filter_by(level=current_level).all()
    for artist in genre_artists:
        try:
            related_artists = sp.artist_related_artists(artist.artist_id)['artists']
            for x in related_artists:
                artist_existed = GenreArtist.query.filter_by(artist_id=x['id'], genre_allmusic=artist.genre_allmusic).first()
                if artist_existed:
                    pass
                else:
                    new_artist_obj = GenreArtist(
                        artist_id=x['id'],
                        followers=x["followers"]["total"],
                        genres=",".join(x["genres"]),
                        image_middle=None if len(x["images"]) == 0 else x["images"][1]["url"],
                        name=x['name'],
                        popularity=x["popularity"],
                        external_urls=x["external_urls"]["spotify"],
                        href=x["href"],
                        uri=x["uri"],
                        level=current_level+1,
                        genre_allmusic=artist.genre_allmusic
                    )
                    db.session.add(new_artist_obj)
                    db.session.commit()
        except Exception as e:
            print(e)

    sp.__del__()
    return "success"


# handler for importing genre-typical tracks to database
@utility_bp.route('/import_tracks_from_csv')
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
