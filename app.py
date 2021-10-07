from flask import Flask, render_template
from general.basic import spotify_basic_bp
from recommendation.recommendation import recommendation_bp
from database import db
from genre_exploration.flow import genre_explore_bp
from dbdw.flow import dbdw_bp
from nudge.flow import nudge_bp
import os
# from rq import Queue
# from worker import conn
# from Utility.utility import scrape_genre_artist, scrape_genre_artist_next_level, \
#     get_artist_top_tracks, import_tracks_from_csv
from flask_debugtoolbar import DebugToolbarExtension


# Force HTTPS connection on server
class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


app = Flask(__name__)
# app.debug = True
app.config.from_object('config')
app.wsgi_app = ReverseProxied(app.wsgi_app)
db.init_app(app)

# Register blueprint for spotify login
app.register_blueprint(spotify_basic_bp)

# Register blueprint for recommendation module
app.register_blueprint(recommendation_bp)

# Register blueprint for Basic Genre Exploration app
app.register_blueprint(genre_explore_bp)

# Register blueprint for the DBDW app
# app.register_blueprint(dbdw_bp)

# Register blueprint for the nudge study
app.register_blueprint(nudge_bp)

toolbar = DebugToolbarExtension(app)

# Initialize queue for worker
# q = Queue(connection=conn, default_timeout=6000)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)


@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response


# Shutdown database session after operations
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


# Render 404 page if the requested url is not found
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404NotFound.html', title='404'), 404

# Function that can run in the background
# @app.route('/run_background')
# def run_background():
#     q.enqueue(spotify_scrape)
#     return render_template("test.html")
#
#
# # scrape from Spotify
# def spotify_scrape():
#     with app.app_context():
#         # scrape_genre_artist_next_level(2)
#         # scrape_genre_artist()
#         # get_artist_top_tracks()
#         import_tracks_from_csv()
