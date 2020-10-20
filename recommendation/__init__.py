from database import db
from general import Track


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

    survey_response = db.relationship('SurveyResponse',
                                      cascade='all, delete-orphan',
                                      backref=db.backref('recommendation_log', lazy=True))

    def __repr__(self):
        return '<RecommendationLog %r-%r-%r>' % (self.id, self.user_id, self.session_id)


# recommended items
class RecTracks(db.Model):
    __tablename__ = 'rec_tracks'
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
    track_id = db.Column(db.VARCHAR, primary_key=True)
    rank = db.Column(db.Integer)

    def __repr__(self):
        return '<RecTracks %r-%r>' % (self.rec_id, self.track_id)
