from flask import url_for, redirect, flash, \
    render_template, request, Blueprint, session
from general import Artist, TopArtists, User, Track, TopTracks, SessionLog, ArtistTracks
from database import db
import uuid

from flask_oauthlib.client import OAuth
import json
import os
import six
import base64
import requests
import time

spotify_basic_bp = Blueprint('spotify_basic_bp', __name__,
                             template_folder='templates')

oauth = OAuth(spotify_basic_bp)
keys = {"CLIENT_ID": "", "CLIENT_SECRET_ID": ""}

try:
    keys = json.load(open('keys.json', 'r'))
except Exception as e:
    print(e)


spotify = oauth.remote_app(
    'spotify',
    consumer_key=os.environ.get('SPOTIFY_CLIENT_ID', keys["CLIENT_ID"]),
    consumer_secret=os.environ.get('SPOTIFY_CLIENT_SECRET', keys["CLIENT_SECRET_ID"]),
    base_url='https://api.spotify.com/',
    request_token_url=None,
    access_token_url='https://accounts.spotify.com/api/token',
    authorize_url='https://accounts.spotify.com/authorize'
)


@spotify.tokengetter
def get_spotify_token():
    return session.get('oauth_token')


@spotify_basic_bp.route('/login/<next_url>')
def login(next_url):
    """
    Controller for login:
    Set authorization scopes: https://developer.spotify.com/documentation/general/guides/scopes/
    Available scopes
        user-read-private user-read-birthdate user-read-email
        playlist-modify-private playlist-read-private playlist-read-collaborative playlist-modify-public
        user-follow-modify user-follow-read
        app-remote-control streaming
        user-read-currently-playing user-modify-playback-state user-read-playback-state
        user-library-modify user-library-read
        user-read-recently-played user-top-read
        user-read-recently-played user-top-read
    :return: user-top-read playlist-modify-private
    """
    if "oauth_token" in session:
        del session["oauth_token"]
    if "userid" in session:
        del session["userid"]

    print("oauth_token" in session)
    if "oauth_token" not in session:
        print("DEBUG: NO TOKEN IN SESSION, REDIRECTING")
        callback = url_for(
            'spotify_basic_bp.authorized',
            next=url_for(next_url),
            _external=True
        )
        print(callback)
        #   define authorization scope
        scope = "user-top-read playlist-modify-private"
        return spotify.authorize(callback=callback, scope=scope, show_dialog=True)
    else:
        print("TOKEN IN SESSION: REDIRECTING")
        # redirect_url = session["redirecturl"] + "?userid=" + session["userid"]
        redirect_url = session["redirecturl"]
        print(redirect_url)
        return redirect(redirect_url)


@spotify_basic_bp.route('/login/authorized')
def authorized():
    #   retrieve basic user information
    print("Redirect from Spotify")
    try:
        next_url = request.args.get('next') or url_for('spotify_basic_bp.index')

        resp = spotify.authorized_response()
        if resp is None:
            flash(u'You denied the request to sign in with your Spotify account')
            return redirect(url_for('spotify_basic_bp.index'))

        session['oauth_token'] = {"access_token": resp['access_token'], "refresh_token": resp['refresh_token'],
                                  "expires_in": resp['expires_in'],
                                  "expires_at": int(time.time()) + resp['expires_in']}
        me = spotify.request('/v1/me/')
        if me.status != 200:
            print('HTTP Status Error: {0}'.format(resp.data))
            return render_template("SpotifyConnectFailed.html")
        else:
            print(me.data)

            if me.data["display_name"] is None:
                display_name = ""
            else:
                display_name = me.data["display_name"]
            if len(me.data["images"]) == 0:
                image = ""
            else:
                image = me.data["images"][0]["url"]

            user = User.query.filter_by(id=me.data["id"]).first()

            if user is None:
                userhash = str(uuid.uuid4())
                user = User(
                    id=me.data["id"],
                    username=display_name,
                    imageurl=image,
                    userhash=userhash,
                    consent_to_share=False)

                db.session.add(user)
                db.session.commit()

            flash('You were signed in as %s' % display_name)
            session["userid"] = user.id

            scrape()
            print(next_url)

            ts = time.time()

            if "subjectid" in session:
                print(session["subjectid"])
                subjectid = session["subjectid"]
            else:
                print("No subject id")
                subjectid = "No subject id"

            session['id'] = str(uuid.uuid4())
            session_log = SessionLog(user_id=session["userid"], id=session['id'], timestamp=ts)

            db.session.add(session_log)
            db.session.commit()

            return redirect(next_url)
    except Exception as e:
        print(e)
        return render_template("SpotifyConnectFailed.html")


@spotify_basic_bp.route('/scrape')
def scrape(limit=50):
    """
    Scrape user top artists
    https://developer.spotify.com/console/get-current-user-top-artists-and-tracks/
    authorization scopes: user-top-read
    :param limit:
    :return:
    """

    terms = ['short', 'medium', 'long']
    # terms = ['short']
    ts = time.time()

    def check_token():
        if "oauth_token" not in session:
            print("authorizing")
            session["redirecturl"] = url_for("scrape")
            return spotify.authorize(url_for("authorized", _external=True))

        if is_token_expired():
            refresh_token = session["oauth_token"]["refresh_token"]
            get_refresh_token(refresh_token)

    for term in terms:
        check_token()
        url = '/v1/me/top/artists?limit=' + str(limit) + '&time_range=' + term + '_term'
        print("url: " + url)
        try:
            top_artists_request = spotify.request(url)

            if top_artists_request.status != 200:
                return "top_artists_request status: " + str(top_artists_request.status), 400
            else:
                top_artists = top_artists_request.data["items"]
                for x in top_artists:
                    artist = Artist.query.filter_by(id=x["id"]).first()

                    if artist:
                        entry = TopArtists.query.filter_by(user_id=session["userid"],
                                                           artist_id=x["id"],
                                                           time_period=term).first()
                        if entry:
                            pass
                        else:
                            new_top_artist_obj = TopArtists(user_id=session["userid"],
                                                            artist_id=x["id"],
                                                            time_period=term,
                                                            timestamp=str(ts)
                                                            )
                            db.session.add(new_top_artist_obj)

                    else:
                        new_artist_obj = Artist(
                            id=x["id"],
                            followers=x["followers"]["total"],
                            genres=",".join(x["genres"]),
                            image_middle=None if len(x["images"]) == 0 else x["images"][1]["url"],
                            name=x["name"],
                            popularity=x["popularity"],
                            external_urls=x["external_urls"]["spotify"],
                            href=x["href"],
                            uri=x["uri"]


                        )
                        new_top_artist_obj = TopArtists(user_id=session["userid"],
                                                        artist_id=x["id"],
                                                        time_period=term,
                                                        timestamp=str(ts),
                                                        artist=new_artist_obj)
                        db.session.add(new_top_artist_obj)
                db.session.commit()
        except Exception as e:
            print(e.args)
            return render_template("SpotifyConnectFailed.html")

    for term in terms:
        check_token()
        url = '/v1/me/top/tracks?limit=' + str(limit) + '&time_range=' + term + '_term'
        print("url: " + url)
        try:
            top_track_request = spotify.request(url)

            if top_track_request.status != 200:
                return "top_track_request status: " + str(top_track_request.status), 400
            else:
                top_tracks = top_track_request.data["items"]
                url = "https://api.spotify.com/v1/audio-features?ids=" + ",".join([x["id"] for x in top_tracks])
                audio_feature_request = spotify.request(url)
                audio_feature_data = audio_feature_request.data["audio_features"]
                track_list = combine_track_features(top_tracks, audio_feature_data)
                library_objects = tracklist2object(track_list)
                for x in library_objects:
                    track = Track.query.filter_by(id=x.id).first()
                    if track:
                        entry = TopTracks.query.filter_by(user_id=session["userid"],
                                                          track_id=x.id,
                                                          time_period=term).first()
                        if entry:
                            pass
                        else:
                            new_toptrack_obj = TopTracks(user_id=session["userid"],
                                                         track_id=x.id,
                                                         time_period=term,
                                                         timestamp=str(ts),
                                                         track=track)
                            db.session.add(new_toptrack_obj)
                    else:
                        new_track_obj = Track(
                            id=x.id, trackname=x.trackname, popularity=x.popularity, preview_url=x.preview_url,
                            track_number=x.track_number, firstartist=x.firstartist, imageurl=x.imageurl,
                            spotifyurl=x.spotifyurl, acousticness=x.acousticness, danceability=x.danceability,
                            duration_ms=x.duration_ms, energy=x.energy, instrumentalness=x.instrumentalness,
                            key=x.key, liveness=x.liveness, loudness=x.loudness,
                            speechiness=x.speechiness, tempo=x.tempo, time_signature=x.time_signature,
                            valence=x.valence
                        )
                        new_toptrack_obj = TopTracks(user_id=session["userid"],
                                                     track_id=x.id, time_period=term,
                                                     timestamp=str(ts), track=new_track_obj)
                        db.session.add(new_toptrack_obj)
                db.session.commit()
        except Exception as e:
            print(e.args)
            return "error", 400
    return "done"


def is_token_expired():
    """
    check if token is expired
    :return: Boolean
    """
    if session["oauth_token"]["expires_at"] - int(time.time()) < 60:
        return True
    return False


def make_refresh_token_headers(client_id, client_secret):
    """
    make refresh token headers
    :param client_id:
    :param client_secret:
    :return: headers for requesting refresh tokens
    """
    auth_header = base64.b64encode(
        six.text_type(client_id + ':' + client_secret).encode('ascii'))
    headers = {'Authorization': 'Basic %s' % auth_header.decode('ascii')}
    return headers


def get_refresh_token(refresh_token):
    """
    get refresh token
    :param refresh_token:
    :return: update oauth_token
    """
    payload = {'refresh_token': refresh_token, 'grant_type': 'refresh_token'}

    headers = make_refresh_token_headers(keys["CLIENT_ID"], keys["CLIENT_SECRET_ID"])
    resp = requests.post(spotify.access_token_url, data=payload, headers=headers)

    if resp.status_code != 200:
        # if False:  # debugging code
        print('debugging')
        print('headers', headers)
    else:
        token_info = resp.json()
        if 'refresh_token' not in token_info:
            session['oauth_token'] = {"access_token": token_info['access_token'], "refresh_token": refresh_token,
                                      "expires_in": token_info['expires_in'],
                                      "expires_at": int(time.time()) + token_info['expires_in']}
        else:
            session['oauth_token'] = {"access_token": token_info['access_token'],
                                      "refresh_token": token_info['refresh_token'],
                                      "expires_in": token_info['expires_in'],
                                      "expires_at": int(time.time()) + token_info['expires_in']}


def combine_track_features(track_recommendations, feature_data):
    """
    combine track features: basic track feature + audio features
    :param track_recommendations:
    :param feature_data:
    :return:
    """
    tracks = {}
    for item in feature_data + track_recommendations:
        if item is not None and "id" in item:
            if item["id"] in tracks:
                tracks[item["id"]].update(item)
            else:
                tracks[item["id"]] = item
    track_list = [val for (_, val) in tracks.items()]
    return track_list


def tracklist2object(track_list):
    """
    tracklist to track object
    :param track_list: a list if tracks
    :return: Track object
    """
    library_objects = []
    for track in track_list:
        try:
            library_objects.append(
                Track(
                    trackname=track["name"],
                    popularity=track["popularity"],
                    preview_url=track["preview_url"],
                    track_number=track["track_number"],
                    id=track["id"],
                    firstartist=track["artists"][0]["name"],
                    imageurl=None if len(track["album"]["images"]) == 0 else track["album"]["images"][1]["url"],
                    spotifyurl=track["external_urls"]["spotify"],
                    acousticness=track["acousticness"],
                    danceability=track["danceability"],
                    duration_ms=track["duration_ms"],
                    energy=track["energy"],
                    instrumentalness=track["instrumentalness"],
                    key=track["key"],
                    liveness=track["liveness"],
                    loudness=track["loudness"],
                    speechiness=track["speechiness"],
                    tempo=track["tempo"],
                    time_signature=track["time_signature"],
                    valence=track["valence"]
                )
            )
        except Exception as e:
            print(e)
            pass
    return library_objects


def generate_playlist(name="demo", description="for demo use", public=False):
    """
    generate a playlist to spotify
    :param name: string, default: "demo"
    :param description: string, default: "for demo use"
    :param public: Boolean, default: False
    :return: playlist_id: string, playlist_url: string
    """
    url = '/v1/users/' + session["userid"] + '/playlists'
    data = {"name": name, "description": description, "public": public}
    try:
        playlist = spotify.post(url, data=data, format='json')
        if playlist.status == 200 or playlist.status == 201:
            playlist_id = playlist.data['id']
            playlist_url = playlist.data['external_urls']['spotify']
            return playlist_id, playlist_url
        else:
            return 'failure in creating new playlist on spotify, error ' + str(playlist.status), 400
    except Exception as e:
        print(e.args)
        return "error", 400


def save_tracks_to_playlist(playlist_id, playlist_url, track_list):
    """
    save a list of tracks to playlist
    :param playlist_id: string
    :param playlist_url: string
    :param track_list: a list of track ids to be added
    :return: playlist_url: string
    """
    url = '/v1/users/' + session["userid"] + '/playlists/' + playlist_id + '/tracks?position=0'
    prefix = "spotify:track:"
    new_track_list = []

    for track in track_list:
        new_track_list.append(prefix + track)
    data = {"uris": new_track_list}
    try:
        new_playlist = spotify.post(url, data=data, format='json')
        if new_playlist.status == 201:
            return playlist_url
        else:
            return 'failure in saving tracks to the new playlist, error ' + str(new_playlist.status), 400
    except Exception as e:
        print(e.args)


def scrape_artist_tracks(artist_id):
    url = '/v1/artists/' + str(artist_id) + '/top-tracks?country=NL'

    artist_track_request = spotify.request(url)

    if artist_track_request.status != 200:
        return "artist_track_request status: " + str(artist_track_request.status), 400
    else:
        artist_tracks = artist_track_request.data["tracks"]
        url = "https://api.spotify.com/v1/audio-features?ids=" + ",".join([x["id"] for x in artist_tracks])
        audio_feature_request = spotify.request(url)
        audio_feature_data = audio_feature_request.data["audio_features"]
        track_list = combine_track_features(artist_tracks, audio_feature_data)
        library_objects = tracklist2object(track_list)
        for x in library_objects:
            track = Track.query.filter_by(id=x.id).first()
            if track:
                    new_artist_track_obj = ArtistTracks(artist_id=artist_id,
                                                        track_id=x.id)
                    db.session.add(new_artist_track_obj)
            else:
                new_track_obj = Track(
                    id=x.id, trackname=x.trackname, popularity=x.popularity, preview_url=x.preview_url,
                    track_number=x.track_number, firstartist=x.firstartist, imageurl=x.imageurl,
                    spotifyurl=x.spotifyurl, acousticness=x.acousticness, danceability=x.danceability,
                    duration_ms=x.duration_ms, energy=x.energy, instrumentalness=x.instrumentalness,
                    key=x.key, liveness=x.liveness, loudness=x.loudness,
                    speechiness=x.speechiness, tempo=x.tempo, time_signature=x.time_signature,
                    valence=x.valence
                )

                new_artist_track_obj = ArtistTracks(artist_id=artist_id,
                                                    track_id=x.id, track=new_track_obj)
                db.session.add(new_artist_track_obj)
        db.session.commit()
