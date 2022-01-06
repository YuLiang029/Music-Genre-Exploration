from database import db


# recommendation logs
class RecommendationLog(db.Model):
    __tablename__ = 'recommendation_log'
    id = db.Column(db.VARCHAR, primary_key=True)
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    start_ts = db.Column(db.FLOAT)
    stop_ts = db.Column(db.FLOAT)
    current_phase = db.Column(db.Integer)
    genre_name = db.Column(db.VARCHAR)
    type = db.Column(db.VARCHAR)
    init_weight = db.Column(db.FLOAT)

    survey_response = db.relationship('SurveyResponse',
                                      cascade='all, delete-orphan',
                                      backref=db.backref('recommendation_log', lazy=True))

    def __repr__(self):
        return '<RecommendationLog %r-%r-%r>' % (self.id, self.user_id, self.session_id)


# table for saving the recommended tracks
class RecTracks(db.Model):
    __tablename__ = 'rec_tracks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'))
    track_id = db.Column(db.VARCHAR)
    rank = db.Column(db.Integer)
    baseline_ranking = db.Column(db.FLOAT)
    personalized_ranking = db.Column(db.FLOAT)
    popularity_ranking = db.Column(db.FLOAT)
    score = db.Column(db.FLOAT)
    weight = db.Column(db.FLOAT)

    def __repr__(self):
        return '<RecTracks %r-%r>' % (self.rec_id, self.track_id)


# table for saving the recommend genres
class RecGenres(db.Model):
    __tablename__ = 'rec_genres'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    rec_genre_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    genre = db.Column(db.VARCHAR)
    score = db.Column(db.FLOAT)
    ts = db.Column(db.FLOAT)

    def __repr__(self):
        return '<RecTracks %r-%r-%r>' % (self.user_id, self.genre, self.score)


class SurveyResponse(db.Model):
    __tablename__ = 'survey_response'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
    item_id = db.Column(db.VARCHAR, primary_key=True)
    value = db.Column(db.VARCHAR)
    stop_ts = db.Column(db.FLOAT)

    def __repr__(self):
        return '<SurveyResponse %r-%r-%r>' % (self.user_id, self.rec_id, self.item_id)


class TrackInteractLog(db.Model):
    __tablename__ = 'track_interact_log'
    id = db.Column(db.INTEGER, autoincrement=True, primary_key=True)
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'))
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    timestamp = db.Column(db.FLOAT)
    track_id = db.Column(db.VARCHAR)


class SliderInteractLog(db.Model):
    __tablename__ = 'slider_interact_log'
    id = db.Column(db.INTEGER, autoincrement=True, primary_key=True)
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'))
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    timestamp = db.Column(db.FLOAT)
    value = db.Column(db.FLOAT)