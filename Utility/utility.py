from general import Track
import pandas as pd
from database import db
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import Spotify
import json
from Utility import GenreArtist


def client_credentials_manager():
    """
    set up client credential manager
    :return: Spotify client credential manager
    """
    keys = json.load(open('keys_scrape.json', 'r'))
    ccm = SpotifyClientCredentials(client_id=keys["CLIENT_ID"], client_secret=keys["CLIENT_SECRET_ID"])
    sp = Spotify(client_credentials_manager=ccm)
    sp.trace = False
    return sp


# scrape the first-level genre-artist from Spotify
def scrape_genre_artist():
    sp = client_credentials_manager()
    l_genre_scrape = ["avant-garde", "blues", "classical",
                      "country", "electronic", "folk",
                      "jazz", "latin", "new-age",
                      "pop-rock", "rap", "reggae",
                      "rnb"]

    for genre in l_genre_scrape:
        print(genre)
        all_music_artist = pd.read_csv("original_genre_artist_from_all_music/" + genre + ".csv",
                                       sep="\n",
                                       names=["artist_name"])

        artist_list = all_music_artist.artist_name.tolist()
        for artist in artist_list:
            try:
                x = sp.search(q=artist, type='artist')['artists']['items'][0]
                if artist == "Goldie":
                    x = sp.artist(artist_id="2SYqJ3uDLLXZNyZdLKBy4M")

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


# scrape the next-level genre-artist
def scrape_genre_artist_next_level(current_level):
    sp = client_credentials_manager()
    genre_artists = GenreArtist.query.filter_by(level=current_level).all()
    num = 0
    for artist in genre_artists:
        num = num + 1
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

        if num % 50 == 0:
            print(num)

    sp.__del__()
    return "success"


# import genre-typical tracks to database
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
