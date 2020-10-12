from database import db


class DBDW_Event(db.Model):
    __tablename__ = 'dbdw_event'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    session = db.Column(db.INTEGER)
    name = db.Column(db.VARCHAR)
    info = db.Column(db.VARCHAR)
    url = db.Column(db.VARCHAR)
    spot_available = db.Column(db.INTEGER)

    def __repr__(self):
        return '<DBDW_Event %r>' % self.id
