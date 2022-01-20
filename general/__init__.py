from database import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.VARCHAR, primary_key=True)
    username = db.Column(db.VARCHAR)
    imageurl = db.Column(db.VARCHAR)
    consent_to_share = db.Column(db.Boolean)
    top_artists = db.relationship('TopArtists', cascade='all')
    subject_id = db.Column(db.VARCHAR)

    msi_response = db.relationship('MsiResponse', cascade='all, delete-orphan', backref="user")

    def __repr__(self):
        return '<User %r>' % self.id


class UserCondition(db.Model):
    __tablename__ = 'user_condition'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    timestamp = db.Column(db.FLOAT)
    condition = db.Column(db.INTEGER)
    default = db.Column(db.VARCHAR)

    def __repr__(self):
        return '<UserCondition %r>' % self.user_id


class TopArtists(db.Model):
    __tablename__ = 'top_artists'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    artist_id = db.Column(db.VARCHAR, db.ForeignKey('artist.id'), primary_key=True)
    time_period = db.Column(db.VARCHAR, primary_key=True)
    timestamp = db.Column(db.FLOAT)
    position = db.Column(db.Integer)
    session_num = db.Column(db.Integer, primary_key=True)
    artist = db.relationship('Artist', cascade='save-update, merge')

    def __repr__(self):
        return '<TopArtists %r-%r>' % (self.user_id, self.artist_id)


class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.VARCHAR, primary_key=True)
    followers = db.Column(db.INTEGER)
    genres = db.Column(db.VARCHAR)
    image_middle = db.Column(db.VARCHAR)
    name = db.Column(db.VARCHAR)
    popularity = db.Column(db.INTEGER)
    external_urls = db.Column(db.VARCHAR)
    href = db.Column(db.VARCHAR)
    uri = db.Column(db.VARCHAR)

    def __repr__(self):
        return '<Artist %r>' % self.id


class Track(db.Model):
    __tablename__ = 'track'
    id = db.Column(db.VARCHAR, primary_key=True)
    trackname = db.Column(db.VARCHAR)
    popularity = db.Column(db.INTEGER)
    preview_url = db.Column(db.VARCHAR)
    track_number = db.Column(db.INTEGER)
    firstartist = db.Column(db.VARCHAR)
    imageurl = db.Column(db.VARCHAR)
    spotifyurl = db.Column(db.VARCHAR)
    acousticness = db.Column(db.FLOAT)
    danceability = db.Column(db.FLOAT)
    duration_ms = db.Column(db.INTEGER)
    energy = db.Column(db.FLOAT)
    instrumentalness = db.Column(db.FLOAT)
    key = db.Column(db.VARCHAR)
    liveness = db.Column(db.FLOAT)
    loudness = db.Column(db.FLOAT)
    speechiness = db.Column(db.FLOAT)
    tempo = db.Column(db.INTEGER)
    time_signature = db.Column(db.INTEGER)
    valence = db.Column(db.FLOAT)

    def to_json(self):
        return dict(
            id=self.id,
            trackname=self.trackname,
            popularity=self.popularity,
            preview_url=self.preview_url,
            track_number=self.track_number,
            firstartist=self.firstartist,
            imageurl=self.imageurl,
            spotifyurl=self.spotifyurl,
            acousticness=self.acousticness,
            danceability=self.danceability,
            duration_ms=self.duration_ms,
            energy=self.energy,
            instrumentalness=self.instrumentalness,
            key=self.key,
            liveness=self.liveness,
            loudness=self.loudness,
            speechiness=self.speechiness,
            tempo=self.tempo,
            time_signature=self.time_signature,
            valence=self.valence)

    def __repr__(self):
        return '<Track %r-%r>' % (self.firstartist, self.trackname)


class TopTracks(db.Model):
    __tablename__ = 'top_tracks'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    track_id = db.Column(db.VARCHAR, db.ForeignKey('track.id'), primary_key=True)
    time_period = db.Column(db.VARCHAR, primary_key=True)
    timestamp = db.Column(db.FLOAT)
    position = db.Column(db.Integer)
    session_num = db.Column(db.Integer, primary_key=True)
    track = db.relationship('Track', cascade='save-update, merge')

    def __repr__(self):
        return '<TopTracks %r-%r>' % (self.user_id, self.track_id)


class MsiResponse(db.Model):
    __tablename__ = 'msi_response'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    item_id = db.Column(db.VARCHAR, primary_key=True)
    value = db.Column(db.VARCHAR)
    start_ts = db.Column(db.FLOAT)
    stop_ts = db.Column(db.FLOAT)

    def __repr__(self):
        return '<MsiResponse %r-%r>' % (self.user_id, self.item_id)


# session logs
class SessionLog(db.Model):
    __tablename__ = 'session_log'
    id = db.Column(db.VARCHAR, primary_key=True)
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    timestamp = db.Column(db.FLOAT)

    def __repr__(self):
        return '<SessionLog %r-%r>' % (self.user_id, self.id)


class ArtistTracks(db.Model):
    __tablename__ = 'artist_tracks'
    artist_id = db.Column(db.VARCHAR, db.ForeignKey('artist.id'), primary_key=True)
    track_id = db.Column(db.VARCHAR, db.ForeignKey('track.id'), primary_key=True)
    track = db.relationship('Track', cascade='save-update, merge')

    def __repr__(self):
        return '<ArtistTracks %r-%r>' % (self.artist_id, self.track_id)


class Playlist(db.Model):
    __tablename__ = 'playlist'
    id = db.Column(db.VARCHAR, primary_key=True)
    name = db.Column(db.VARCHAR)
    description = db.Column(db.VARCHAR)
    url = db.Column(db.VARCHAR)
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'))
    rec_id = db.Column(db.VARCHAR, db.ForeignKey('recommendation_log.id'))
    session_id = db.Column(db.VARCHAR, db.ForeignKey('session_log.id'))
    timestamp = db.Column(db.FLOAT)

    def __repr__(self):
        return '<Playlist %r>' % self.id


class SavedTracks(db.Model):
    __tablename__ = 'saved_tracks'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    track_id = db.Column(db.VARCHAR, primary_key=True)
    timestamp = db.Column(db.FLOAT)
    session_num = db.Column(db.Integer, primary_key=True)
    added_at = db.Column(db.VARCHAR)
    track_name = db.Column(db.VARCHAR)
    preview_url = db.Column(db.VARCHAR)
    popularity = db.Column(db.Integer)
    artist_id = db.Column(db.VARCHAR)
    artist_name = db.Column(db.VARCHAR)

    def __repr__(self):
        return '<SavedTracks %r-%r>' % (self.user_id, self.track_id)


class FollowedArtist(db.Model):
    __tablename__ = 'followed_artist'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    artist_id = db.Column(db.VARCHAR, db.ForeignKey('artist.id'), primary_key=True)
    timestamp = db.Column(db.FLOAT)
    session_num = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    artist = db.relationship('Artist', cascade='save-update, merge')

    def __repr__(self):
        return '<FollowedArtist %r-%r>' % (self.user_id, self.artist_id)


class RecentTracks(db.Model):
    __tablename__ = 'recent_tracks'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    track_id = db.Column(db.VARCHAR, primary_key=True)
    timestamp = db.Column(db.FLOAT)
    session_num = db.Column(db.Integer, primary_key=True)
    played_at = db.Column(db.VARCHAR, primary_key=True)
    track_name = db.Column(db.VARCHAR)
    preview_url = db.Column(db.VARCHAR)
    popularity = db.Column(db.Integer)
    artist_id = db.Column(db.VARCHAR)
    artist_name = db.Column(db.VARCHAR)

    def __repr__(self):
        return '<RecentTracks %r-%r>' % (self.user_id, self.track_id)
