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

    def __repr__(self):
        return '<RecommendationLog %r-%r-%r>' % (self.id, self.user_id, self.session_id)


# recommended items
class RecTracks(db.Model):
    __tablename__ = 'rec_tracks'
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
    track_id = db.Column(db.VARCHAR, db.ForeignKey('track.id'), primary_key=True)
    rank = db.Column(db.Integer)
    track = db.relationship(Track)

    def __repr__(self):
        return '<RecTracks %r-%r>' % (self.rec_id, self.track_id)


# survey
class SurveyResponse(db.Model):
    __tablename__ = 'survey_response'
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User')
    genre_name = db.Column(db.VARCHAR)
    item_id = db.Column(db.VARCHAR, primary_key=True)
    value = db.Column(db.VARCHAR)
    start_ts = db.Column(db.FLOAT)
    stop_ts = db.Column(db.FLOAT)

    def __repr__(self):
        return '<SurveyResponseRec %r-%r-%r>' % (self.userid, self.recuid, self.itemid)
