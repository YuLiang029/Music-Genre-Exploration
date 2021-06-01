from flask import session, jsonify, Blueprint, request, render_template
import time
import uuid
from general import TopTracks, TopArtists, User
from database import db
import pandas as pd
import os
import numpy as np
from sklearn.mixture import GaussianMixture
from recommendation import RecommendationLog, RecTracks, RecGenres, TrackInteractLog, SliderInteractLog
from collections import Counter
import operator
from functools import reduce
from sklearn.feature_extraction.text import CountVectorizer
import networkx as nx
import pickle

recommendation_bp = Blueprint('recommendation_bp', __name__,
                              template_folder='templates')

audio_features = ['danceability', 'valence', 'energy', 'liveness', 'speechiness', 'acousticness']
track_features = ['id', 'trackname', 'popularity'] + audio_features
track_features1 = track_features + ['baseline_ranking', 'sum_rank_ranking']
rec_track_features = track_features1 + ['ranking_score', 'weight']
audio_features_exp = ['danceability', 'valence', 'energy', 'acousticness']

with open(os.path.join(os.path.dirname(recommendation_bp.root_path), 'recommendation/tags.pkl'), 'rb') as f:
    l_tags = pickle.load(f)

with open(os.path.join(os.path.dirname(recommendation_bp.root_path), 'recommendation/nodes.pkl'), 'rb') as f:
    l_nodes = pickle.load(f)

G = nx.read_gpickle(os.path.join(os.path.dirname(recommendation_bp.root_path), 'recommendation/tags.gpickle'))


# Genre suggestion function based on Personalized PageRank
@recommendation_bp.route('/genre_suggestion_new')
def genre_suggestion_new():
    # get genre artists
    l_genre = ["avant-garde", "blues", "classical",
               "country", "electronic", "folk",
               "jazz", "latin", "new-age",
               "pop-rock", "rap", "reggae",
               "rnb"]

    # print(l_tags)

    # check if the genre suggestions have been generated
    rec_genres = RecGenres.query.filter_by(user_id=session["userid"], ).order_by(RecGenres.score.desc()).all()

    if rec_genres:
        l_genre_score_sorted = []
        for item in rec_genres:
            l_genre_score_sorted.append(item.genre)
        return jsonify(l_genre_score_sorted)

    # get a user's top artists
    top_artists = TopArtists.query.filter_by(user_id=session["userid"]).all()

    # return error if non top artists exist
    if not top_artists:
        # error message
        return jsonify("error")

    # get top artists' genre
    user_corpus = []
    for item in top_artists:
        # print(item.artist.genres)
        user_corpus.append(item.artist.genres)
    if len(user_corpus) == 0:
        return jsonify("error")

    user_vectorizer = CountVectorizer(token_pattern='(?u)[a-zA-Z][a-z-& ]+')
    user_result = user_vectorizer.fit_transform(user_corpus).todense()
    yu_cols = user_vectorizer.get_feature_names()
    df_user_tag = pd.DataFrame(user_result, columns=yu_cols)
    user_dict = df_user_tag.sum(axis=0).to_dict()
    t_dict = {}

    for nodes in l_nodes:
        t_dict[nodes] = 0

    flag = 0
    for nodes in user_dict:
        if nodes in t_dict:
            t_dict[nodes] = t_dict[nodes] + user_dict[nodes]
            flag = 1

    if flag == 0:
        return jsonify("error")

    # distribute weight to source code rather than using a uniform distribution
    n_zero_nodes = 0
    n_nonzero_nodes = 0
    sum_nonzero_nodes = 0

    for nodes in t_dict:
        if t_dict[nodes] == 0:
            n_zero_nodes = n_zero_nodes + 1
        else:
            n_nonzero_nodes = n_nonzero_nodes + 1
            sum_nonzero_nodes = sum_nonzero_nodes + t_dict[nodes]

    tag_score = nx.pagerank(G, personalization=t_dict)

    dict_genre_score = {}
    l_rec_genres = []
    for i in range(len(l_genre)):
        genre_score = 0
        genre_tags = l_tags[i]

        j = 0
        for tag in genre_tags:
            if tag in tag_score:
                j = j + 1
                genre_score = genre_score + tag_score[tag]

        dict_genre_score[l_genre[i]] = genre_score/j
        rec_genres = RecGenres(user_id=session["userid"], genre=l_genre[i],
                               score=dict_genre_score[l_genre[i]], ts=time.time())
        l_rec_genres.append(rec_genres)

    db.session.add_all(l_rec_genres)
    db.session.commit()
    print(dict_genre_score)
    l_genre_score_sorted = sorted(dict_genre_score, key=dict_genre_score.get, reverse=True)
    print(l_genre_score_sorted)
    return jsonify(l_genre_score_sorted)


# Genre suggestion function based on simple cosine similarity
@recommendation_bp.route('/genre_suggestion')
def genre_suggestion():
    # check if the genre suggestions have been generated
    rec_genres = RecGenres.query.filter_by(user_id=session["userid"],).order_by(RecGenres.score.desc()).all()

    if rec_genres:
        l_genre_score_sorted = []
        for item in rec_genres:
            l_genre_score_sorted.append(item.genre)
        return jsonify(l_genre_score_sorted)

    # get a user's top artists
    top_artists = TopArtists.query.filter_by(user_id=session["userid"]).all()

    # return error if non top artists exist
    if not top_artists:
        # error message
        error_message = "error"
        return jsonify(error_message)

    # get top artists' genre
    l_user_artist = []
    for item in top_artists:
        l_user_artist.extend(item.artist.genres.split(","))
    c_user = Counter(l_user_artist)
    dict_user = dict(c_user)

    # get genre artists
    l_genre = ["avant-garde", "blues", "classical",
               "country", "electronic", "folk",
               "jazz", "latin", "new-age",
               "pop-rock", "rap", "reggae",
               "rnb"]
    dict_genre_score = {}
    for genre in l_genre:
        genre_artists = pd.read_csv(os.path.join(os.path.dirname(recommendation_bp.root_path),
                                                 'genre_artists/key_artist_1_2/' + genre + ".csv"), sep=";")

        df_genre = genre_artists[genre_artists["genre_allmusic"] == genre]
        l_genre_artist = df_genre.dropna(subset=['genres']).genres.str.split(",").tolist()
        l_genre_artist_flat = reduce(operator.add, l_genre_artist)

        c_genre = Counter(l_genre_artist_flat)
        dict_genre = dict(c_genre)

        # Preparation for genre suggestion
        # 1. construct numpy array for both genre and user with all keywords
        genre_combined = set(dict_genre.keys()).union(set(dict_user.keys()))
        user_preference = {}
        genre_profile = {}

        for item in genre_combined:
            user_preference[item] = 0
            genre_profile[item] = 0

        for item in dict_user:
            user_preference[item] = dict_user[item]
        np_user = np.fromiter(user_preference.values(), dtype="float")

        for item in dict_genre:
            genre_profile[item] = dict_genre[item]
        np_genre = np.fromiter(genre_profile.values(), dtype="float")
        # 2. compute cosine similarity
        cos_m_genre = cosine_sim(np_user, np_genre)
        dict_genre_score[genre] = cos_m_genre
        rec_genres = RecGenres(user_id=session["userid"], genre=genre, score=cos_m_genre, ts=time.time())
        db.session.add(rec_genres)

    db.session.commit()
    print(dict_genre_score)
    l_genre_score_sorted = sorted(dict_genre_score, key=dict_genre_score.get, reverse=True)
    print(l_genre_score_sorted)
    return jsonify(l_genre_score_sorted)


def cosine_sim(np1: np.ndarray, np2: np.ndarray):
    score = np.dot(np1, np2) / (np.linalg.norm(np1) * np.linalg.norm(np2))
    return score


# Get tracks from a music genre (can be sorted by popularity)
@recommendation_bp.route('/genre_top_tracks/<genre>/<sort>/<num>')
def genre_top_tracks(genre, sort, num):
    """
    genre recommendation by popularity: request handler
    :return: recommended tracks in json
    """
    genre_df = get_genre_recommendation_by_popularity(genre)

    if sort == "sorted":
        genre_df = genre_df.sort_values(by=['popularity'], ascending=False)

    if num != "all":
        genre_df = genre_df[:int(num)]

    # Only retain relevant columns
    genre_df = genre_df[['popularity', 'energy', 'valence', 'acousticness',
                         'danceability', 'speechiness', 'trackname',
                         'firstartist']]

    return jsonify(genre_df.to_dict('records'))


def get_ranking_score(v_sum_rank_ranking, v_baseline_ranking, len_genre_df, weight):
    ranking_score = weight * (len_genre_df - v_sum_rank_ranking + 1) + (1 - weight) * (
                len_genre_df - v_baseline_ranking + 1)
    return ranking_score


# Get recommended tracks from the requested music genre with the requested weight (0.0-1.0)
# for balancing representativeness and personalization
@recommendation_bp.route('/genre_recommendation_exp')
def genre_recommendation_exp():
    """
    genre recommendation handler for the user experiment
    :return:
    """
    ts = time.time()
    session['rec_id'] = str(uuid.uuid4())
    genre_name = request.args.get('genre')
    weight = float(request.args.get('weight'))
    print(weight)

    print('selected genre is {}'.format(genre_name))

    # TODO read users' current phase in the within-subject design.
    #  The variable current phase is only available for within-subject design
    # current_phase = 0

    recommendation_log = RecommendationLog(user_id=session["userid"], genre_name=genre_name,
                                           start_ts=ts, session_id=session['id'], id=session['rec_id'])

    db.session.add(recommendation_log)
    db.session.commit()

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

        return genre_df

    genre_df1 = get_genre_recommendation_by_mix(weight=weight)

    top_tracks = genre_df1[:300]

    for index, row in top_tracks.iterrows():
        rec_tracks = RecTracks(rec_id=session['rec_id'], track_id=row["id"], rank=index)
        db.session.add(rec_tracks)
        db.session.commit()

    top_tracks = top_tracks.replace(np.nan, '')

    top_tracks_list = top_tracks.to_dict('records')
    return jsonify(top_tracks_list)


# Get top-10 recommended tracks from a requested music genre with a list of weight values
# (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0) for balancing representativeness and personalization
@recommendation_bp.route('/genre_recommendation_exp_multiple')
def genre_recommendation_exp_multiple():
    ts = time.time()
    session['rec_id'] = str(uuid.uuid4())
    genre_name = request.args.get('genre')
    weight = float(request.args.get('weight'))
    print(weight)

    print('selected genre is {}'.format(genre_name))

    recommendation_log = RecommendationLog(user_id=session["userid"], genre_name=genre_name,
                                           start_ts=ts, session_id=session['id'], id=session['rec_id'])

    db.session.add(recommendation_log)
    db.session.commit()

    def get_mix_multiple_top(l_weight: list):
        genre_df = get_genre_recommendation_by_preference(genre_name, by_preference=False)

        if not isinstance(genre_df, pd.DataFrame):
            return genre_df

        # genre_df = genre_df.assign(baseline_ranking=genre_df['popularity'].rank(ascending=False))
        genre_df = genre_df.assign(sum_rank_ranking=genre_df['sum_rank'].rank(ascending=False))

        weight_df = pd.DataFrame(columns=track_features1)

        for w in l_weight:
            ranking_score = get_ranking_score(genre_df['sum_rank_ranking'].values,
                                              genre_df['baseline_ranking'].values,
                                              len(genre_df), w)
            genre_df['ranking_score_' + str(w)] = ranking_score

            genre_df = genre_df.sort_values(
                by=['ranking_score_' + str(w), 'trackname'], ascending=[False, True]).reset_index(drop=True)
            top = genre_df[:10]
            top["weight"] = w
            top = top.rename(columns={'ranking_score_' + str(w): 'ranking_score'})[rec_track_features]
            weight_df = weight_df.append(top, ignore_index=False)

        weight_df = weight_df.reset_index()
        return weight_df

    genre_df1 = get_mix_multiple_top(l_weight=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

    if not isinstance(genre_df1, pd.DataFrame):
        return jsonify("error")
    else:
        top_tracks = genre_df1
        # print(genre_df1)

        l_rec_trakcs = []
        for index, row in top_tracks.iterrows():
            # rec_tracks = RecTracks(rec_id=session['rec_id'], track_id=row["id"], rank=row["index"])
            rec_tracks = RecTracks(rec_id=session['rec_id'], track_id=row["id"],
                                   rank=row["index"],
                                   baseline_ranking=row['baseline_ranking'],
                                   personalized_ranking=row['sum_rank_ranking'],
                                   score=row['ranking_score'], weight=row['weight'])
            l_rec_trakcs.append(rec_tracks)

        db.session.add_all(l_rec_trakcs)
        db.session.commit()

        top_tracks_list = top_tracks.to_dict('records')
        return jsonify(top_tracks_list)


# Popularity-based recommendations: get the most popular tracks from the genre
def get_genre_recommendation_by_popularity(genre_name):
    """
    get recommendation by popularity within a certain genre: function
    :param genre_name:
    :return:
    """
    genre_basline_folder = os.path.join(os.path.dirname(recommendation_bp.root_path), 'genre_baseline_1_2_four_features')
    genre_csv_path = os.path.join(genre_basline_folder, genre_name + ".csv")
    genre_df = pd.read_csv(genre_csv_path)
    genre_df = genre_df.sort_values(by=['popularity'], ascending=False)

    print('popularity return dataframe length is {}'.format(len(genre_df)))

    # return the recommendation ranked by popularity
    return genre_df


# Personalized approaches: get the most personalized tracks of the genre based on users'
# preferences on the audio features.
def get_genre_recommendation_by_preference(genre_name=None, track_df=None, by_preference=True):
    """
    get recommendation by preference within a certain genre: function
    :param genre_name
    :param track_df
    :param by_preference
    :return: th_genre_df if th_filter else genre_df
    """

    if genre_name is not None:
        genre_df_folder = os.path.join(os.path.dirname(recommendation_bp.root_path), 'genre_baseline_1_2_four_features')
        genre_csv_path = os.path.join(genre_df_folder, genre_name + ".csv")
        genre_df = pd.read_csv(genre_csv_path).drop_duplicates(keep='first')
    else:
        genre_df = track_df.drop_duplicates(subset=['id'], keep='first')

    """Gaussian filter function"""
    ls = np.linspace(0, 1, 1000)

    def gaussian(x, mu, sig):
        return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

    _filter = gaussian(ls, 0.5, .05)
    """Gaussian filter function"""

    def get_map(x):
        y = x.astype(float)*999
        return np.rint(y).astype(int)

    def get_sum_rank(v_danceability_crank, v_valence_crank, v_energy_crank,
                     v_acousticness_crank, len_genre_df):

        # sum_rank = len_genre_df + 1 - (v_danceability_crank + v_valence_crank +
        #                                v_energy_crank + v_liveness_crank +
        #                                v_speechiness_crank + v_acousticness_crank)/6.0

        sum_rank = len_genre_df + 1 - (v_danceability_crank + v_valence_crank +
                                       v_energy_crank + v_acousticness_crank) / 4.0

        return sum_rank

    """Check if user profile has already modeled"""
    str_return = check_user_model()
    user_folder_path = os.path.join(os.path.dirname(recommendation_bp.root_path), 'user_folder')
    current_user = User.query.filter_by(id=session["userid"]).first().userhash

    if (str_return == "no top tracks") or (str_return == "not enough top tracks"):
        return str_return
    elif (str_return == "successfully build the model") or (str_return == "is the model"):
        try:
            for audio_feature in audio_features_exp:
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
                # elif audio_feature == 'liveness':
                #     genre_df['liveness_convolve'] = l_convolve
                # elif audio_feature == 'speechiness':
                #     genre_df['speechiness_convolve'] = l_convolve
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
        # liveness_crank=genre_df['liveness_convolve'].rank(ascending=False),
        # speechiness_crank=genre_df['speechiness_convolve'].rank(ascending=False),
        acousticness_crank=genre_df['acousticness_convolve'].rank(ascending=False))

    len_genre_df = len(genre_df)

    sum_rank = get_sum_rank(v_danceability_crank=genre_df['danceability_crank'].values,
                            v_valence_crank=genre_df['valence_crank'].values,
                            v_energy_crank=genre_df['energy_crank'].values,
                            # v_liveness_crank=genre_df['liveness_crank'].values,
                            # v_speechiness_crank=genre_df['speechiness_crank'].values,
                            v_acousticness_crank=genre_df['acousticness_crank'].values,
                            len_genre_df=len_genre_df)

    genre_df['sum_rank'] = sum_rank
    genre_df = genre_df.sort_values(by=['sum_rank', 'trackname'], ascending=[False, True]).reset_index(drop=True)
    print('preference-based genre dataframe length is {}'.format(len(genre_df)))

    if by_preference:
        return genre_df
    else:
        return genre_df


# Check if the user model exist or not.
# If not: build the user model, else: get recommendations from the existed user model
def check_user_model():
    userid = session["userid"]

    user_obj = TopTracks.query.filter_by(user_id=userid).all()

    user_json = [x.track.to_json() for x in user_obj]

    user_folder_path = os.path.join(os.path.dirname(recommendation_bp.root_path), 'user_folder')
    print(user_folder_path)

    current_user = User.query.filter_by(id=session["userid"]).first().userhash

    try:
        toptrack_df = pd.DataFrame.from_dict(user_json, orient='columns').drop_duplicates(subset=['id'],
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
            # os.path.isfile(os.path.join(user_folder_path, current_user + "_liveness.npy")) and
            # os.path.isfile(os.path.join(user_folder_path, current_user + "_speechiness.npy")) and
            os.path.isfile(os.path.join(user_folder_path, current_user + "_acousticness.npy"))
    ):
        return "is the model"

    else:
        try:
            for audio_feature in audio_features_exp:
                p1 = gmm_density1(toptrack_df[[audio_feature]].values)
                np.save(os.path.join(user_folder_path, current_user + "_" + audio_feature), p1)
            return "successfully build the model"
        except Exception as e:
            print(e)
            return "error"


# The Gaussian Mixture Model for building the user profile on audio features
def gmm_density1(X):
    """
    Gaussian Mixture Model
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


# Log functionality for track interactions
@recommendation_bp.route('/log_track_interact', methods=['POST'])
def log_track_interact():
    if request.method == 'POST':
        track_interact_log = TrackInteractLog(
            user_id=session["userid"],
            rec_id=session["rec_id"],
            session_id=session["id"],
            timestamp=time.time(),
            track_id=request.form["track_id"],
        )
        db.session.add(track_interact_log)
        db.session.commit()
        print("Stored interaction with track {}".format(request.form["track_id"]))
        return "done"


# Log functionality for slider interactions
@recommendation_bp.route('/log_slider_interact', methods=['POST'])
def log_slider_interact():
    if request.method == 'POST':
        slider_interact_log = SliderInteractLog(
            user_id=session["userid"],
            rec_id=session["rec_id"],
            timestamp=time.time(),
            session_id=session["id"],
            value=request.form["slider_val"]
        )
        db.session.add(slider_interact_log)
        db.session.commit()
        return "done"

