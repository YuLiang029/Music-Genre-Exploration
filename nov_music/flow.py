from flask import render_template, redirect, url_for
from flask import Blueprint

nov_bp = Blueprint('nov_bp', __name__, template_folder='templates')


@nov_bp.route('/')
def index():
    return render_template('main.html')


@nov_bp.route('/test_url')
def test_url():
    return render_template("test.html")

