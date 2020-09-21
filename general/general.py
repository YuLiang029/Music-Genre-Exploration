from flask import Blueprint, render_template, session, url_for, redirect, jsonify, request, flash
from database import db
from flask_oauthlib.client import OAuth
from flask import session

import json
import os
import time
import uuid

import six
import base64
import requests

general_bp = Blueprint('general_bp', __name__,
                       template_folder='templates')

oauth = OAuth(general_bp)
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


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.VARCHAR, primary_key=True)
    username = db.Column(db.VARCHAR)
    imageurl = db.Column(db.VARCHAR)
    userhash = db.Column(db.VARCHAR)
    consent_to_share = db.Column(db.Boolean)
    top_artists = db.relationship('TopArtists', cascade='all')

    def __repr__(self):
        return '<User %r>' % self.id


class TopArtists(db.Model):
    __tablename__ = 'top_artists'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    artist_id = db.Column(db.VARCHAR, db.ForeignKey('artist.id'), primary_key=True,)
    time_period = db.Column(db.VARCHAR, primary_key=True)
    timestamp = db.Column(db.FLOAT)
    artist = db.relationship('Artist', cascade='save-update, merge')

    def __repr__(self):
        return '<TopArtists %r-%r>' % (self.userid, self.artistid)


class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.VARCHAR, primary_key=True)
    followers = db.Column(db.INTEGER)
    genres = db.Column(db.VARCHAR)
    image_middle = db.Column(db.VARCHAR)
    name = db.Column(db.VARCHAR)
    popularity = db.Column(db.INTEGER)
    external_urls = db.Column(db.VARCHAR)
    href = db.Column(db.VARCHAR)
    uri = db.Column(db.VARCHAR)

    def __repr__(self):
        return '<Artist %r>' % self.id

    
@general_bp.route('/')
def index():
    return render_template('index.html')


@general_bp.route('/login')
def login():
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
            'general_bp.authorized',
            next=url_for("general_bp.test_url"),
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


@general_bp.route('/login/authorized')
def authorized():
    #   retrieve basic user information
    print("Redirect from Spotify")
    try:
        next_url = request.args.get('next') or url_for('general_bp.index')

        resp = spotify.authorized_response()
        if resp is None:
            flash(u'You denied the request to sign in with your Spotify account')
            return redirect(url_for('general_bp.index'))

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
            return redirect(next_url)
    except Exception as e:
        print(e)
        return render_template("SpotifyConnectFailed.html")


@general_bp.route('/test_url')
def test_url():
    return render_template("test.html")


@general_bp.route('/scrape')
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


