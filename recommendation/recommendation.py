from flask import session, jsonify, Blueprint
import time
import uuid
from general import TopTracks, User
from database import db
import pandas as pd
import os
import numpy as np
from sklearn.mixture import GaussianMixture
from recommendation import RecommendationLog, RecTracks


recommendation_bp = Blueprint('recommendation_bp', __name__,
                              template_folder='templates')


@recommendation_bp.route('/genre_recommendation_exp')
def genre_recommendation_exp():
    """
    genre recommendation handler for the user experiment
    :return:
    """
    ts = time.time()
    session['recuid'] = str(uuid.uuid4())
    genre_name = "blues"
    weight = 0.5
    print(weight)

    print('selected genre is {}'.format(genre_name))

    # @TODO read users' current phase in the within-subject design
    current_phase = 0

    recommendation_log = RecommendationLog(user_id=session["userid"], genre_name=genre_name, current_phase=current_phase,
                                           start_ts=ts, session_id=str(uuid.uuid4()), id=session['recuid'])

    db.session.add(recommendation_log)
    db.session.commit()

    def get_ranking_score(v_sum_rank_ranking, v_baseline_ranking, len_genre_df, weight):
        ranking_score = weight*(len_genre_df - v_sum_rank_ranking + 1) + (1 - weight)*(len_genre_df - v_baseline_ranking + 1)
        return ranking_score

    def get_genre_recommendation_by_mix(weight=0.5):
        genre_df = get_genre_recommendation_by_preference(genre_name, by_preference=False)

        print(genre_df)

        if not isinstance(genre_df, pd.DataFrame):
            return genre_df

        genre_df = genre_df.assign(baseline_ranking=genre_df['popularity'].rank(ascending=False))
        genre_df = genre_df.assign(sum_rank_ranking=genre_df['sum_rank'].rank(ascending=False))

        ranking_score = get_ranking_score(genre_df['sum_rank_ranking'].values,
                                          genre_df['baseline_ranking'].values,
                                          len(genre_df), weight)
        genre_df['ranking_score'] = ranking_score

        genre_df = genre_df.sort_values(
            by=['ranking_score', 'trackname'], ascending=[False, True]).reset_index(drop=True)
        print('mix genre dataframe length is {}'.format(len(genre_df)))

        return genre_df[:300]

    genre_df1 = get_genre_recommendation_by_mix(weight=weight)

    top_tracks = genre_df1[:300]

    for index, row in top_tracks.iterrows():
        rec_tracks = RecTracks(rec_id=session['recuid'], track_id=row["id"], rank=index)
        db.session.add(rec_tracks)
        db.session.commit()

    top_tracks = top_tracks.replace(np.nan, '')

    top_tracks_list = top_tracks.to_dict('records')
    return jsonify(top_tracks_list)


def get_genre_recommendation_by_popularity(genre_name):
    """
    get recommendation by popularity within a certain genre: function
    :param genre_name:
    :return:
    """
    genre_basline_folder = os.path.join(os.path.dirname(recommendation_bp.root_path), 'genre_baseline')
    genre_csv_path = os.path.join(genre_basline_folder, genre_name + ".csv")
    genre_df = pd.read_csv(genre_csv_path)

    print ('popularity return dataframe length is {}'.format(len(genre_df)))

    return genre_df[:300]


def get_genre_recommendation_by_preference(genre_name, by_preference=True):
    """
    get recommendation by preference within a certain genre: function
    :param genre_name:
    :param th_filter: default = True
    :return: th_genre_df if th_filter else genre_df
    """
    audio_features = ['danceability', 'valence', 'energy', 'liveness', 'speechiness', 'acousticness']
    track_features = ['id', 'trackname', 'preview_url', 'popularity', 'firstartist', 'imageurl', 'spotifyurl'] + audio_features

    genre_df_folder = os.path.join(os.path.dirname(recommendation_bp.root_path), 'genre_baseline')
    genre_csv_path = os.path.join(genre_df_folder, genre_name + ".csv")
    genre_df = pd.read_csv(genre_csv_path)[track_features].drop_duplicates(keep='first')

    """Gaussian filter function"""
    ls = np.linspace(0, 1, 1000)

    def gaussian(x, mu, sig):
        return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

    _filter = gaussian(ls, 0.5, .05)
    """Gaussian filter function"""

    def get_map(x):
        y = x.astype(float)*999
        return np.rint(y).astype(int)

    def get_sum_rank(v_danceability_crank, v_valence_crank, v_energy_crank, v_liveness_crank, v_speechiness_crank,
                     v_acousticness_crank, len_genre_df):

        sum_rank = len_genre_df + 1 - (v_danceability_crank + v_valence_crank +
                                       v_energy_crank + v_liveness_crank +
                                       v_speechiness_crank + v_acousticness_crank)/6.0
        return sum_rank

    """Check if user profile has already modeled"""
    str_return = check_user_model()
    user_folder_path = os.path.join(os.path.dirname(recommendation_bp.root_path), 'user_folder')
    current_user = User.query.filter_by(id=session["userid"]).first().userhash

    if (str_return == "no top tracks") or (str_return == "not enough top tracks"):
        return str_return
    elif (str_return == "successfully build the model") or (str_return == "is the model"):
        try:
            for audio_feature in audio_features:
                p1 = np.load(os.path.join(user_folder_path, current_user + "_" + audio_feature + ".npy"))
                _map = np.convolve(p1, _filter, mode='same') / 1000

                np_match = get_map(genre_df[audio_feature].values)
                l_convolve = [_map[x] for x in np_match]

                if audio_feature == 'danceability':
                    genre_df['danceability_convolve'] = l_convolve
                elif audio_feature == 'valence':
                    genre_df['valence_convolve'] = l_convolve
                elif audio_feature == 'energy':
                    genre_df['energy_convolve'] = l_convolve
                elif audio_feature == 'liveness':
                    genre_df['liveness_convolve'] = l_convolve
                elif audio_feature == 'speechiness':
                    genre_df['speechiness_convolve'] = l_convolve
                elif audio_feature == 'acousticness':
                    genre_df['acousticness_convolve'] = l_convolve

        except Exception as e:
            print (e)
    else:
        return str_return

    """Ranking for convolve scores"""
    genre_df = genre_df.assign(
        danceability_crank=genre_df['danceability_convolve'].rank(ascending=False),
        valence_crank=genre_df['valence_convolve'].rank(ascending=False),
        energy_crank=genre_df['energy_convolve'].rank(ascending=False),
        liveness_crank=genre_df['liveness_convolve'].rank(ascending=False),
        speechiness_crank=genre_df['speechiness_convolve'].rank(ascending=False),
        acousticness_crank=genre_df['acousticness_convolve'].rank(ascending=False))

    len_genre_df = len(genre_df)

    sum_rank = get_sum_rank(v_danceability_crank=genre_df['danceability_crank'].values,
                            v_valence_crank=genre_df['valence_crank'].values,
                            v_energy_crank=genre_df['energy_crank'].values,
                            v_liveness_crank=genre_df['liveness_crank'].values,
                            v_speechiness_crank=genre_df['speechiness_crank'].values,
                            v_acousticness_crank=genre_df['acousticness_crank'].values,
                            len_genre_df=len_genre_df)

    genre_df['sum_rank'] = sum_rank
    genre_df = genre_df.sort_values(by=['sum_rank', 'trackname'], ascending=[False, True]).reset_index(drop=True)
    print('preference-based genre dataframe length is {}'.format(len(genre_df)))

    if by_preference:
        return genre_df[:300]
    else:
        return genre_df


def check_user_model():
    audio_features = ['danceability', 'valence', 'energy', 'liveness', 'speechiness', 'acousticness']
    track_features = ['id', 'trackname', 'preview_url', 'popularity', 'firstartist', 'imageurl', 'spotifyurl'] + audio_features
    userid = session["userid"]

    user_obj = TopTracks.query.filter_by(user_id=userid).all()

    user_json = [x.track.to_json() for x in user_obj]

    user_folder_path = os.path.join(os.path.dirname(recommendation_bp.root_path), 'user_folder')
    print(user_folder_path)

    current_user = User.query.filter_by(id=session["userid"]).first().userhash

    try:
        toptrack_df = pd.DataFrame.from_dict(user_json, orient='columns')[track_features].drop_duplicates(subset=['id'],
                                                                                                          keep="first")
    except KeyError:
        str_return = "no top tracks"
        return str_return

    if len(toptrack_df.index) < 20:
        str_return = "not enough top tracks"
        return str_return

    if (
            os.path.isfile(os.path.join(user_folder_path, current_user + "_danceability.npy")) and
            os.path.isfile(os.path.join(user_folder_path, current_user + "_valence.npy")) and
            os.path.isfile(os.path.join(user_folder_path, current_user + "_energy.npy")) and
            os.path.isfile(os.path.join(user_folder_path, current_user + "_liveness.npy")) and
            os.path.isfile(os.path.join(user_folder_path, current_user + "_speechiness.npy")) and
            os.path.isfile(os.path.join(user_folder_path, current_user + "_acousticness.npy"))
    ):
        return "is the model"

    else:
        try:
            for audio_feature in audio_features:
                p1 = gmm_density1(toptrack_df[[audio_feature]].values)
                np.save(os.path.join(user_folder_path, current_user + "_" + audio_feature), p1)
            return "successfully build the model"
        except Exception as e:
            print (e)
            return "error"


def gmm_density1(X):
    """
    Gaussian Mixture Model
    :param y:
    :param X:
    :return: Y, Z
    """
    n_components_range = range(1, 10)
    cv_types = ['spherical', 'tied', 'diag', 'full']
    lowest_bic = np.infty
    bic = []
    n_c = 0
    best_cv = ''
    P = [[x] for x in np.linspace(0, 1, 1000)]

    for cv_type in cv_types:
        for i in n_components_range:
            gmm = GaussianMixture(n_components=i, covariance_type=cv_type)
            gmm.fit(X)
            bic.append(gmm.bic(X))
            if bic[-1] < lowest_bic:
                lowest_bic = bic[-1]
                best_gmm = gmm
                n_c = i
                best_cv = cv_type
    print('lowest bic is ' + str(lowest_bic))
    print('n components ' + str(n_c))
    print(best_cv)

    # x1 = best_gmm.score_samples(X)
    p1 = np.exp(best_gmm.score_samples(P))

    return p1

