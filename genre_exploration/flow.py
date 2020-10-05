from flask import render_template, redirect, session, Blueprint, request, jsonify
from general import User, TopTracks
from general.basic import is_token_expired, get_refresh_token, generate_playlist, save_tracks_to_playlist
from recommendation.recommendation import get_genre_recommendation_by_popularity
import time


genre_explore_bp = Blueprint('genre_explore_bp', __name__, template_folder='templates')


@genre_explore_bp.route('/')
def index():
    return render_template('main.html')


@genre_explore_bp.route('/test_url')
def test_url():
    return redirect('select_genre')


@genre_explore_bp.route('/select_genre')
def select_genre():
    return render_template("select_genre.html")


@genre_explore_bp.route('/explore_genre')
def explore_genre():

    # Infer the experimental condition
    control = 1
    vis = 1

    return render_template('explore_genre.html',
                           genre=request.args.get('genre'),
                           weight=request.args.get('weight'),
                           control=control, vis=vis)


@genre_explore_bp.route('/genre_top_tracks')
def genre_top_tracks():
    """
    genre recommendation by popularity: request handler
    :return: recommended tracks in json
    """
    genre_name = request.args.get('genre')
    genre_df = get_genre_recommendation_by_popularity(genre_name)
    genre_df = genre_df.sort_values(by=['popularity'], ascending=False)

    # Only retain relevant columns
    genre_df = genre_df[['energy', 'valence', 'popularity', 'trackname', 'firstartist']]

    return jsonify(genre_df[:100].to_dict('records'))


@genre_explore_bp.route('/generate_playlist_spotify/<genre>')
def generate_playlist_spotify(genre):
    """
    if "oauth_token" not in session:
    print("authorizing")
    session["redirecturl"] = url_for("scrape")
    return (spotify.authorize(url_for("authorized", _external=True)))
    """
    ts = time.time()
    recuid = session['recuid']

    tracks = request.args.get('tracks')
    # print tracks
    track_list = tracks.split(',')

    name = "Explored genre: " + genre

    """refresh token"""
    if is_token_expired():
        refresh_token = session["oauth_token"]["refresh_token"]
        get_refresh_token(refresh_token)

    playlist_id, playlist_url = generate_playlist(name=name, description=name)

    playlist_url = save_tracks_to_playlist(playlist_id, playlist_url, track_list)

    # spotify_playlist = Playlist(id=playlist_id, name=name, description=name, url=playlist_url,
    #                             recuid=recuid, timestamp=ts, userid=session["userid"], sessionuid=session["uid"])
    #
    # db.session.add(spotify_playlist)
    # db.session.commit()

    return "done"

