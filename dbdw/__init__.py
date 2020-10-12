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
