from database import db


class UserPlaylistSession (db.Model):
    __tablename__ = 'user_playlist_session'
    id = db.Column(db.VARCHAR, primary_key=True)
    playlist_id = db.Column(db.VARCHAR, db.ForeignKey('playlist.id'))
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'))
    timestamp = db.Column(db.FLOAT)
    session_num = db.Column(db.Integer)
    weight = db.Column(db.FLOAT)

    def __repr__(self):
        return '<SessionPlaylist %r>' % self.id


class ShowHistoryLog (db.Model):
    __tablename__ = 'show_history_log'
    id = db.Column(db.INTEGER, autoincrement=True, primary_key=True)
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'))
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    timestamp = db.Column(db.FLOAT)
    value = db.Column(db.Boolean)
