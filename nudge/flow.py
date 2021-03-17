from flask import render_template, redirect, Blueprint, request

nudge_bp = Blueprint('nudge_bp', __name__, template_folder='templates')


@nudge_bp.route('/')
def index():
    return render_template('main2.html')


@nudge_bp.route('/redirect_from_main2')
def redirect_from_main2():
    return redirect('select_genre2')


@nudge_bp.route('/select_genre2')
def select_genre2():
    return render_template("select_genre2.html")


@nudge_bp.route('/explore_genre2')
def explore_genre2():

    # Infer the experimental condition
    personalized = 1

    return render_template('explore_genre2.html',
                           genre=request.args.get('genre'),
                           weight=request.args.get('weight'),
                           personalized=personalized)

