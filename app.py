from flask import Flask, render_template
from general.basic import spotify_basic_bp
from recommendation.recommendation import recommendation_bp
from database import db
from genre_exploration.flow import genre_explore_bp
from dbdw.flow import dbdw_bp
from nudge.flow import nudge_bp
import os
from rq import Queue
from worker import conn
from Utility.utility import scrape_genre_artist, scrape_genre_artist_next_level, get_artist_top_tracks

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)
app.register_blueprint(spotify_basic_bp)
app.register_blueprint(recommendation_bp)
# app.register_blueprint(genre_explore_bp)
# app.register_blueprint(dbdw_bp)
app.register_blueprint(nudge_bp)


q = Queue(connection=conn, default_timeout=4000)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)


@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response


@app.route('/run_background')
def run_background():
    q.enqueue(spotify_scrape)
    return render_template("test.html")


# scrape from Spotify
def spotify_scrape():
    with app.app_context():
        # scrape_genre_artist_next_level(2)
        # scrape_genre_artist()
        get_artist_top_tracks()
