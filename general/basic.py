from flask import url_for, redirect, flash, \
    render_template, request, Blueprint, session, jsonify
from general import Artist, TopArtists, User, Track, TopTracks, SessionLog, ArtistTracks, MsiResponse, Playlist
from database import db
import uuid

from flask_oauthlib.client import OAuth
import json
import os
import six
import base64
import requests
import time
import re

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
        next_url = request.args.get('next') or url_for('index')

        resp = spotify.authorized_response()
        if resp is None:
            flash(u'You denied the request to sign in with your Spotify account')
            return redirect(url_for('index'))

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

            scrape(limit=50, type="tracks")
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
def scrape(limit=50, type="tracks"):
    """
    Scrape user top artists
    https://developer.spotify.com/console/get-current-user-top-artists-and-tracks/
    authorization scopes: user-top-read
    :param limit:
    :return:
    """

    if type == "tracks":
        track_scrape(limit=limit)
    elif type == "artists":
        artist_scrape(limit=limit)
    else:
        track_scrape(limit=limit)
        artist_scrape(limit=limit)
    return "done"


def artist_scrape(limit=50):
    ts = time.time()
    terms = ['short', 'medium', 'long']

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


def track_scrape(limit=50):
    ts = time.time()
    terms = ['short', 'medium', 'long']

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


def check_token():
    if "oauth_token" not in session:
        print("authorizing")
        session["redirecturl"] = url_for("scrape")
        return spotify.authorize(url_for("authorized", _external=True))

    if is_token_expired():
        refresh_token = session["oauth_token"]["refresh_token"]
        get_refresh_token(refresh_token)


@spotify_basic_bp.route('/user_top_tracks')
def user_top_tracks():
    user_id = session["userid"]
    top_tracks = TopTracks.query.filter_by(user_id=user_id).all()
    return jsonify([x.track.to_json() for x in top_tracks])


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


@spotify_basic_bp.route('/msi_survey', methods=["GET", "POST"])
def msi_survey():
    if request.method == "GET":
        responses = User.query.filter_by(id=session["userid"]).first().msi_response
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
                    "name": "email",
                    "type": "text",
                    "inputType": "email",
                    "title": "Your contact email:",
                    "isRequired": "true",
                    "validators": [{
                        "type": "email"
                    }]
                }, {
                    "name": "age",
                    "type": "text",
                    "title": "Your age (years):",
                    "isRequired": "true"
                }, {
                    "name": "gender",
                    "type": "dropdown",
                    "title": "Your gender:",
                    "isRequired": "true",
                    "colCount": 0,
                    "choices": [
                        "male",
                        "female",
                        "other"
                    ]
                }]
            }, {
                "questions": [{
                    "type": "matrix",
                    "name": "Active Engagement",
                    "title": "Below some questions how you relate to music. "
                             "Please indicate to what extent you agree or disagree with each statement.",
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
                        {"value": "1", "text": "I spend a lot of my free time doing music-related activities."},
                        {"value": "2", "text": "I enjoy writing about music, for example on blogs and forums."},
                        {"value": "3", "text": "I'm intrigued by musical styles I'm not familiar with and want "
                                               "to find out more."},
                        {"value": "4", "text": "I often read or search the internet for things related to music."},
                        {"value": "5", "text": "I don't spend much of my disposable income on music."},
                        {"value": "6", "text": "Music is kind of an addiction for me - I couldn't live without it."},
                        {"value": "7", "text": "I keep track of new of music that I come across (e.g. new artists "
                                               "or recordings)."}
                    ]
                }, {
                    "type": "dropdown",
                    "name": "8",
                    "title": "I have attended _ live music events as an audience member in the past twelve months.",
                    "isRequired": "true",
                    "colCount": 0,
                    "choices": [
                        "0",
                        "1",
                        "2",
                        "3",
                        "4-6",
                        "7-10",
                        "11 or more"
                    ]
                }, {
                    "type": "dropdown",
                    "name": "9",
                    "title": "I listen attentively to music for __ per day.",
                    "isRequired": "true",
                    "colCount": 0,
                    "choices": [
                        "0-15 minutes",
                        "15-30 minutes",
                        "30-60 minutes",
                        "60-90 minutes",
                        "2 hours",
                        "2-3 hours",
                        "4 hours or more"
                    ]
                }]
            }, {
                "questions": [{
                    "type": "matrix",
                    "name": "Emotions",
                    "title": "Please indicate to what extent you agree or disagree with the following statements",
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
                        {"value": "10",
                         "text": "I sometimes choose music that can trigger shivers down my spine."},
                        {"value": "11", "text": "Pieces of music rarely evoke emotions for me."},
                        {"value": "12", "text": "I often pick certain music to motivate or excite me."},
                        {"value": "13",
                         "text": "I am able to identify what is special about a given musical piece."},
                        {"value": "14",
                         "text": "I am able to talk about the emotions that a piece of music evokes for me."},
                        {"value": "15", "text": "Music can evoke my memories of past people and places."}
                    ]
                }]
            }],
            "completedHtml": "Redirecting to the next page..."
        }

        survey_config = {
            'title': 'Musical sophistication survey',
            'description': 'The music sophistication survey makes us know your music expertise better.',
            'next_url': url_for('dbdw_bp.event_explore')
        }

        print(surveydata)
        return render_template('survey.html', survey=survey, surveydata=surveydata, survey_config=survey_config)

    if request.method == "POST":
        stop_ts = time.time()

        user = User.query.filter_by(id=session["userid"]).first()
        user.msi_response[:] = [
            MsiResponse(user_id=user.id, user=user,
                        item_id=item, value=request.form[item], stop_ts=stop_ts) for item in
            request.form]
        db.session.commit()
        return "done"


@spotify_basic_bp.route('/generate_playlist_spotify/<genre>')
def generate_playlist_spotify(genre):
    """
    if "oauth_token" not in session:
    print("authorizing")
    session["redirecturl"] = url_for("scrape")
    return (spotify.authorize(url_for("authorized", _external=True)))
    """
    rec_id = session['rec_id']

    tracks = request.args.get('tracks')
    track_list = tracks.split(',')

    """refresh token"""
    if is_token_expired():
        refresh_token = session["oauth_token"]["refresh_token"]
        get_refresh_token(refresh_token)

    playlist_id, playlist_url = generate_playlist(name=genre, description=genre)

    playlist_url = save_tracks_to_playlist(playlist_id, playlist_url, track_list)

    spotify_playlist = Playlist(id=playlist_id,
                                name=genre,
                                description=genre,
                                url=playlist_url,
                                rec_id=rec_id,
                                timestamp=time.time(),
                                user_id=session["userid"],
                                session_id=session["id"])

    db.session.add(spotify_playlist)
    db.session.commit()

    return "done"

