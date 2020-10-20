from database import db


class DBDWEvent(db.Model):
    __tablename__ = 'dbdw_event'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    session = db.Column(db.INTEGER)
    name = db.Column(db.VARCHAR)
    info = db.Column(db.VARCHAR)
    url = db.Column(db.VARCHAR)
    spot_available = db.Column(db.INTEGER)

    def __repr__(self):
        return '<DBDWEvent %r>' % self.id


class UserCondition(db.Model):
    __tablename__ = 'user_condition'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    timestamp = db.Column(db.FLOAT)
    condition = db.Column(db.INTEGER)
    default = db.Column(db.VARCHAR)

    def __repr__(self):
        return '<UserCondition %r>' % self.user_id


# class RecEvent(db.Model):
#     __tablename__ = 'rec_event'
#     rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
#     event_id = db.Column(db.VARCHAR, primary_key=True)
#     rec_scores = db.Column(db.FLOAT)
#     event_valence = db.Column(db.FLOAT)
#     event_energy = db.Column(db.FLOAT)
#     session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
#     user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
#     timestamp = db.Column(db.FLOAT)
#
#     def __repr__(self):
#         return '<RecEvent %r-%r>' % (self.user_id, self.event_id)


class RecStream(db.Model):
    __tablename__ = 'rec_stream'
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
    stream_name = db.Column(db.VARCHAR, primary_key=True)
    rec_scores = db.Column(db.FLOAT)
    stream_valence = db.Column(db.FLOAT)
    stream_energy = db.Column(db.FLOAT)
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    timestamp = db.Column(db.FLOAT)

    def __repr__(self):
        return '<RecStream %r-%r-%r>' % (self.user_id, self.stream_name, self.rec_scores)


# class RegisterEvent(db.Model):
#     __tablename__ = 'register_event'
#     user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
#     session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
#     rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
#     event_id = db.Column(db.VARCHAR, primary_key=True)
#     event_session = db.Column(db.VARCHAR, primary_key=True)
#     timestamp = db.Column(db.FLOAT)
#
#     def __repr__(self):
#         return '<RegisterEvent %r-%r>' % (self.user_id, self.event_id)

