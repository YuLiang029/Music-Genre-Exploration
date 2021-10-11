from database import db


class RecEvent(db.Model):
    __tablename__ = 'rec_event'
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)
    event_id = db.Column(db.VARCHAR, primary_key=True)
    rec_scores = db.Column(db.FLOAT)
    event_valence = db.Column(db.FLOAT)
    event_energy = db.Column(db.FLOAT)
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    timestamp = db.Column(db.FLOAT)

    def __repr__(self):
        return '<RecEvent %r-%r>' % (self.user_id, self.event_id)


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


class SelectedStream (db.Model):
    __tablename__ = 'selected_stream'
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    timestamp = db.Column(db.FLOAT)
    stream_name = db.Column(db.VARCHAR, primary_key=True)
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)

    def __repr__(self):
        return '<SelectedStream %r-%r>' % (self.user_id, self.stream_name)


class SelectedEvent (db.Model):
    __tablename__ = 'selected_event'
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    timestamp = db.Column(db.FLOAT)
    event_name = db.Column(db.VARCHAR, primary_key=True)
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'), primary_key=True)

    def __repr__(self):
        return '<SelectedEvent %r-%r>' % (self.user_id, self.event_name)


class Events (db.Model):
    __tablename__ = 'events'
    event_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    event_name = db.Column(db.VARCHAR)
    event_timeslot = db.Column(db.VARCHAR)
    spots_available = db.Column(db.INTEGER)

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


class ImgRatings(db.Model):
    __tablename__ = 'img_ratings'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    img_id = db.Column(db.VARCHAR)
    rating = db.Column(db.VARCHAR)
    ts = db.Column(db.FLOAT)

    def __repr__(self):
        return '<ImgRatings %r-%r>' % (self.id, self.user_id)
