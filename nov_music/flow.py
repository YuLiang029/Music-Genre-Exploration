from general.basic import spotify_basic_bp
from flask import Blueprint, render_template

nov_bp = Blueprint('nov_bp', __name__,
                   template_folder='templates')


@nov_bp.route('/')
def index():
    return render_template('nov_main.html')


@nov_bp.route('/spotify_login')
def spotify_login():
    spotify_basic_bp.route('/login')
