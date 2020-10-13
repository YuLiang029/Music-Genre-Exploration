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

    def __repr__(self):
        return '<UserCondition %r>' % self.user_id


class RecEvent(db.Model):
    __tablename__ = 'rec_event'
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
    event_id = db.Column(db.VARCHAR, primary_key=True)
    availability = db.Column(db.Boolean)
    rec_scores = db.Column(db.FLOAT)
    event_valence = db.Column(db.FLOAT)
    event_energy = db.Column(db.FLOAT)
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    timestamp = db.Column(db.FLOAT)

    def __repr__(self):
        return '<RecEvent %r-%r>' % (self.id, self.user_id)

