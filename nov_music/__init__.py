from general import Track, Artist
from database import db


class Event(db.Model):
    __tablename__ = 'event'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    name = db.Column(db.VARCHAR)
    info = db.Column(db.VARCHAR)
    url = db.Column(db.VARCHAR)
    img_url = db.Column(db.VARCHAR)
    artists = db.Column(db.VARCHAR)

    event_artists = db.relationship('EventArtists', cascade='all')

    def __repr__(self):
        return '<Event %r>' % self.id


class EventArtists(db.Model):
    __tablename__ = 'event_artists'
    event_id = db.Column(db.ForeignKey('event.id'), primary_key=True)
    artist_id = db.Column(db.ForeignKey('artist.id'), primary_key=True)

    artist = db.relationship(Artist, cascade='save-update, merge')

    def __repr__(self):
        return '<EventArtists %r-%r>' % (self.event_id, self.artist_id)

    def get_artist_id_only(self):
        return self.artist_id


class EventTracks(db.Model):
    __tablename__ = 'event_tracks'
    event_id = db.Column(db.ForeignKey('event.id'), primary_key=True)
    track_id = db.Column(db.ForeignKey('track.id'), primary_key=True)

    track = db.relationship(Track, cascade='save-update, merge')

    def __repr__(self):
        return '<EventTracks %r-%r>' % (self.event_id, self.track_id)


