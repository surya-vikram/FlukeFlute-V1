from FlukeFlute import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete='CASCADE'))


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    roles = db.relationship('Role', secondary='user_role', backref='users')
    stage_name = db.Column(db.String(20))
    pfp_path = db.Column(db.String(100))
    bio = db.Column(db.String(255))
    is_flagged = db.Column(db.Boolean, default=False)   
    tracks = db.relationship('Track', backref='creator')
    albums = db.relationship('Album', backref='creator')
    playlists = db.relationship('Playlist', backref='creator')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)
    
    def make_creator(self, stage_name, bio, pfp):        
        creator_role = Role.query.filter_by(name='Creator').first()
        self.stage_name = stage_name
        self.bio = bio
        self.pfp_path = pfp
        self.roles.append(creator_role)
        db.session.commit()

    def make_admin(self):
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role not in self.roles:
            self.roles.append(admin_role)
            db.session.commit()

    def popularity(self):
        return sum([track.playback_count for track in self.tracks])


class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    lyrics = db.Column(db.Text)
    audio_path = db.Column(db.String, nullable=False)
    playback_count = db.Column(db.Integer, default=0)
    release_date = db.Column(db.Date, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    album_id = db.Column(db.Integer, db.ForeignKey('album.id', ondelete='CASCADE'))
    language_id = db.Column(db.Integer, db.ForeignKey('language.id', ondelete='CASCADE'))
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id', ondelete='CASCADE'))
    ratings = db.relationship('User', secondary='rating')

    def increment_playback(self):
        self.playback_count += 1
        db.session.commit()

    @staticmethod
    def trending(limit=10):
        return Track.query.order_by(Track.playback_count.desc()).limit(limit).all()

    def avg_rating(self):
        ratings = [rating.rating_value for rating in Rating.query.filter_by(track_id=self.id).all()]
        return round(sum(ratings) / len(ratings), 1) if ratings else 0.0

    @staticmethod
    def top_rated(limit=10):
        return (db.session.query(Track)
                .join(Rating, Rating.track_id == Track.id)
                .group_by(Track.id)
                .order_by(func.avg(Rating.rating_value).desc())
                .limit(limit)
                .all())


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id', ondelete='CASCADE'), nullable=False)
    rating_value = db.Column(db.Integer, nullable=False)


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    tracks = db.relationship('Track', secondary='playlist_track')


class PlaylistTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id', ondelete='CASCADE'))
    track_id = db.Column(db.Integer, db.ForeignKey('track.id', ondelete='CASCADE'))


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cover_path = db.Column(db.String, default="album.jpg")
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    tracks = db.relationship('Track', backref='album')


class Language(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    tracks = db.relationship('Track', backref='language')


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    tracks = db.relationship('Track', backref='genre')



