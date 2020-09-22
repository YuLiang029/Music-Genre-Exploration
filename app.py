from flask import Flask
from general.basic import spotify_basic_bp
from text_analyze.spotify_tagme import spotify_tagme_bp
from database import db
from nov_music.flow import nov_bp

import os

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)
app.register_blueprint(spotify_basic_bp)
app.register_blueprint(nov_bp)
# app.register_blueprint(spotify_tagme_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)


@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response


