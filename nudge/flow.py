from flask import render_template, redirect, Blueprint, request, jsonify
from recommendation.recommendation import get_genre_recommendation_by_popularity


nudge_bp = Blueprint('nudge_bp', __name__, template_folder='templates')


@nudge_bp.route('/')
def index():
    return render_template('main2.html')


@nudge_bp.route('/redirect_from_main')
def redirect_from_main():
    return redirect('select_genre2')


@nudge_bp.route('/select_genre2')
def select_genre():
    return render_template("select_genre2.html")


@nudge_bp.route('/explore_genre2')
def explore_genre2():

    # Infer the experimental condition
    personalized = 1

    return render_template('explore_genre2.html',
                           genre=request.args.get('genre'),
                           weight=request.args.get('weight'),
                           personalized=personalized)


@nudge_bp.route('/genre_top_tracks')
def genre_top_tracks():
    """
    genre recommendation by popularity: request handler
    :return: recommended tracks in json
    """
    genre_name = request.args.get('genre')
    genre_df = get_genre_recommendation_by_popularity(genre_name)

    # Only retain relevant columns
    genre_df = genre_df[['popularity', 'energy', 'valence', 'acousticness', 'danceability', 'speechiness', 'trackname', 'firstartist']]
    print(genre_df)

    return jsonify(genre_df.to_dict('records'))


# @genre_explore_bp.route('/generate_playlist_spotify/<genre>')
# def generate_playlist_spotify(genre):
#     """
#     if "oauth_token" not in session:
#     print("authorizing")
#     session["redirecturl"] = url_for("scrape")
#     return (spotify.authorize(url_for("authorized", _external=True)))
#     """
#     ts = time.time()
#     recuid = session['recuid']
#
#     tracks = request.args.get('tracks')
#     # print tracks
#     track_list = tracks.split(',')
#
#     name = "Explored genre: " + genre
#
#     """refresh token"""
#     if is_token_expired():
#         refresh_token = session["oauth_token"]["refresh_token"]
#         get_refresh_token(refresh_token)
#
#     playlist_id, playlist_url = generate_playlist(name=name, description=name)
#
#     playlist_url = save_tracks_to_playlist(playlist_id, playlist_url, track_list)
#
#     # spotify_playlist = Playlist(id=playlist_id, name=name, description=name, url=playlist_url,
#     #                             recuid=recuid, timestamp=ts, userid=session["userid"], sessionuid=session["uid"])
#     #
#     # db.session.add(spotify_playlist)
#     # db.session.commit()
#
#     return "done"

