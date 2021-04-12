from general import Track, ArtistTracks
import pandas as pd
from database import db
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import Spotify
import json
from Utility import GenreArtist, GenreTracks


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


# get artist top tracks
def get_artist_top_tracks():
    sp = client_credentials_manager()
    l_genre_scrape = ["avant-garde", "blues", "classical",
                      "country", "electronic", "folk",
                      "jazz", "latin", "new-age",
                      "pop-rock", "rap", "reggae",
                      "rnb"]

    # folder = "key_artist_1"
    folder = "key_artist_1_2"
    for genre in l_genre_scrape:
        print(genre)

        df_genre_artists = pd.read_csv("genre_artists/" + folder + "/" + genre + ".csv", sep=";")
        l_genre_artists = df_genre_artists.artist_id.unique().tolist()

        for artist_id in l_genre_artists:
            try:
                top_tracks = sp.artist_top_tracks(artist_id=artist_id, country="NL")['tracks']
                for top_track in top_tracks:
                    track_id = top_track['id']
                    track = Track.query.filter_by(id=track_id).first()
                    if track:
                        entry = GenreTracks.query.filter_by(track_id=track_id, genre_allmusic=genre).first()
                        artist_track_entry = ArtistTracks.query.filter_by(artist_id=artist_id,
                                                                          track_id=track_id).first()
                        if not entry:
                            new_genre_track = GenreTracks(track_id=track_id, genre_allmusic=genre, track=track)
                            db.session.add(new_genre_track)

                        if not artist_track_entry:
                            new_artist_track = ArtistTracks(artist_id=artist_id, track_id=track_id, track=track)
                            db.session.add(new_artist_track)

                    else:
                        trackname = top_track['name']
                        popularity = top_track['popularity']
                        preview_url = top_track['preview_url']
                        track_number = top_track['track_number']
                        firstartist= top_track["artists"][0]["name"]
                        imageurl = None if len(top_track["album"]["images"]) == 0 else top_track["album"]["images"][1]["url"]
                        spotifyurl = top_track["external_urls"]["spotify"]

                        audio_features = sp.audio_features(tracks=[track_id])[0]
                        acousticness = audio_features["acousticness"]
                        danceability = audio_features["danceability"]
                        duration_ms = audio_features["duration_ms"]
                        energy = audio_features["energy"]
                        instrumentalness = audio_features["instrumentalness"]
                        key = audio_features["key"]
                        liveness = audio_features["liveness"]
                        loudness = audio_features["loudness"]
                        speechiness = audio_features["speechiness"]
                        tempo = audio_features["tempo"]
                        time_signature = audio_features["time_signature"]
                        valence = audio_features["valence"]

                        new_track_obj = Track(
                            id=track_id, trackname=trackname, popularity=popularity, preview_url=preview_url,
                            track_number=track_number, firstartist=firstartist, imageurl=imageurl,
                            spotifyurl=spotifyurl, acousticness=acousticness, danceability=danceability,
                            duration_ms=duration_ms, energy=energy, instrumentalness=instrumentalness,
                            key=key, liveness=liveness, loudness=loudness, speechiness=speechiness,
                            tempo=tempo, time_signature=time_signature, valence=valence
                        )
                        new_genre_track = GenreTracks(track_id=track_id, genre_allmusic=genre, track=new_track_obj)
                        new_artist_track = ArtistTracks(artist_id=artist_id, track_id=track_id, track=new_track_obj)

                        db.session.add(new_artist_track)
                        db.session.add(new_genre_track)
                    db.session.commit()
            except Exception as e:
                print(e)


# import genre-typical tracks to database
def import_tracks_from_csv():
    l_genre = ["avant-garde", "blues", "classical",
               "country", "electronic", "folk",
               "jazz", "latin", "new-age",
               "pop-rock", "rap", "reggae",
               "rnb"]
    folder = "genre_baseline_1_2_four_features"

    for genre in l_genre:
        df = pd.read_csv(folder + "/" + genre + ".csv", encoding='utf8')

        for index, row in df.iterrows():
            track = Track.query.filter_by(id=row.id).first()
            if track:
                entry = GenreTracks.query.filter_by(track_id=row.id, genre_allmusic=genre).first()

                if not entry:
                    new_genre_track = GenreTracks(track_id=row.id, genre_allmusic=genre, track=track,
                                                  baseline_score=row.baseline_score)
                    db.session.add(new_genre_track)

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
                new_genre_track = GenreTracks(track_id=row.id, genre_allmusic=genre, track=new_track_obj,
                                              baseline_score=row.baseline_score)

                if index % 100 == 0:
                    print(index)
                db.session.add(new_genre_track)
                db.session.add(new_track_obj)
            db.session.commit()