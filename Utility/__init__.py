from database import db


class GenreArtist(db.Model):
    __tablename__ = 'genre_artist'
    id = db.Column(db.INTEGER, autoincrement=True, primary_key=True)
    artist_id = db.Column(db.VARCHAR)
    followers = db.Column(db.INTEGER)
    genres = db.Column(db.VARCHAR)
    image_middle = db.Column(db.VARCHAR)
    name = db.Column(db.VARCHAR)
    popularity = db.Column(db.INTEGER)
    external_urls = db.Column(db.VARCHAR)
    href = db.Column(db.VARCHAR)
    uri = db.Column(db.VARCHAR)

    # columns for storing information of genre-typical artists
    level = db.Column(db.INTEGER)
    genre_allmusic = db.Column(db.VARCHAR)

    def __repr__(self):
        return '<GenreArtist %r-%r>' % (self.artist_id, self.genre_allmusic)


class GenreTracks(db.Model):
    __tablename__ = 'genre_track'
    id = db.Column(db.INTEGER, autoincrement=True, primary_key=True)
    track_id = db.Column(db.VARCHAR, db.ForeignKey('track.id'))
    genre_allmusic = db.Column(db.VARCHAR)
    baseline_score = db.Column(db.FLOAT)
    track = db.relationship('Track', cascade='save-update, merge')

    def __repr__(self):
        return '<GenreTrack %r-%r>' % (self.track_id, self.genre_allmusic)