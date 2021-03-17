from flask import render_template, redirect, session, Blueprint, request, jsonify
from general import User, TopTracks
from general.basic import is_token_expired, get_refresh_token, generate_playlist, save_tracks_to_playlist
from recommendation.recommendation import get_genre_recommendation_by_popularity
import time


genre_explore_bp = Blueprint('genre_explore_bp', __name__, template_folder='templates')


@genre_explore_bp.route('/')
def index():
    return render_template('main.html')


@genre_explore_bp.route('/redirect_from_main')
def redirect_from_main():
    return redirect('select_genre')


@genre_explore_bp.route('/select_genre')
def select_genre():
    return render_template("select_genre.html")


@genre_explore_bp.route('/explore_genre')
def explore_genre():

    # Set the condition
    control = 1
    vis = 1

    return render_template('explore_genre.html',
                           genre=request.args.get('genre'),
                           weight=request.args.get('weight'),
                           control=control, vis=vis)

