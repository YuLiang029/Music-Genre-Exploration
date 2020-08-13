from flask import Blueprint, render_template, session, url_for, redirect, jsonify, request, flash
from database import db
from flask_oauthlib.client import OAuth
from flask import session

import json
import os
import time
import uuid

general_bp = Blueprint('general_bp', __name__,
                       template_folder='templates')

oauth = OAuth(general_bp)
keys = {"CLIENT_ID": "", "CLIENT_SECRET_ID": ""}
try:
    keys = json.load(open('keys.json', 'r'))
except Exception as e:
    print (e)


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

    def __repr__(self):
        return '<User %r>' % self.id


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
        print (callback)
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
            print 'HTTP Status Error: {0}'.format(resp.data)
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
            print (next_url)
            return redirect(next_url)
    except Exception as e:
        print (e)
        return render_template("SpotifyConnectFailed.html")


@general_bp.route('/test_url')
def test_url():
    return render_template("test.html")

