from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, TextAreaField, IntegerField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Regexp
from flask_wtf.file import FileField, FileAllowed, FileRequired
from FlukeFlute.models import User, Genre, Language, Track
from flask_login import current_user

class RegisterForm(FlaskForm):
    name = StringField(label='Name', validators=[Length(max=40), DataRequired(message='Name field is empty'), Regexp('^[A-Za-z ]*$', message='Only letters and spaces allowed in the name.')])
    username = StringField(label='Username', validators=[Length(max=20), DataRequired(message='You must give username'), Regexp('^[a-zA-Z0-9_]*$', message='Only letters, numbers, and underscores allowed in the username.')])
    email_address = StringField(label='Email Address', validators=[Email(), DataRequired('Fill out email')])
    password1 = PasswordField(label='Password', validators=[Length(min=6, max=40), DataRequired('Password should not be empty')])
    password2 = PasswordField(label='Confirm Password', validators=[EqualTo('password1', message="Password doesn't match"), DataRequired('Confirm your password')])
    submit = SubmitField(label='Create Account')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different username.')

    def validate_email_address(self, field):
        email_address = User.query.filter_by(email=field.data).first()
        if email_address:
            raise ValidationError('This email address is already registered. Please use a different email address.')


class LoginForm(FlaskForm):
    username = StringField(label='User Name', validators=[DataRequired(message='username cannot be empty')])
    password = PasswordField(label='Password', validators=[DataRequired('password is must')])
    submit = SubmitField(label='Sign in')


class CreatorForm(FlaskForm):
    stage_name = StringField(label='Stage name', validators=[DataRequired(message='stage name is must')])
    pfp = FileField(label='Upload PFP', validators=[FileAllowed(['jpg', 'jpeg', 'png']), FileRequired(message='pfp not chosen')])
    bio = TextAreaField(label='Write your bio', validators=[DataRequired('bio should not be empty'), Length(min=25, max=255, message="Field must be between 25 and 255 characters.")])
    submit = SubmitField(label='Sign up')

languages = [ (lang.id, lang.name) for lang in Language.query.all()]
genres = [ (genre.id, genre.name) for genre in Genre.query.all()]

class SongUploadForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired(message='Title is must')])
    language = SelectField(label='Language', validators=[DataRequired(message='Choose a Language')], choices=languages)
    genre = SelectField(label='Genre', validators=[DataRequired(message='Select a Genre')], choices=genres)
    audio = FileField(label='Song File', validators=[FileRequired('Audio file not chosen'), FileAllowed(['mp3'])])
    lyrics = TextAreaField(label='Lyrics')
    submit = SubmitField(label='Upload')


class CreateAlbumForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired(message='Title cannot be empty')])
    cover = FileField(label='Upload Cover', validators=[ FileAllowed(['jpg', 'jpeg', 'png']), FileRequired(message='Image not chosen')])
    tracks = SelectMultipleField(label='Select Tracks', validators=[ DataRequired('You must select atleast one track or Upload a new one first')], coerce=int, choices=lambda: [(track.id, track.title) for track in Track.query.filter_by(creator_id=current_user.id, album_id=None).all()])
    description = TextAreaField(label='Description')
    submit = SubmitField(label='Create')


class CreatePlaylistForm(FlaskForm):
    name = StringField(label='Title', validators=[DataRequired(message='Title cannot be empty')])
    tracks = SelectMultipleField(label='Select Tracks', validators=[DataRequired('You must select atleast one track')], coerce=int, choices=lambda: [(track.id, track.title) for track in Track.query.all()])
    submit = SubmitField(label='Submit')


class AddGenreForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired(message='Genre name field cannot be empty')])
    submit = SubmitField(label='Submit')


class AddLangugeForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired(message='Language name field cannot be empty')])
    submit = SubmitField(label='Submit')


class UpdateTrackForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired(message='Title is must')])
    language = SelectField(label='Language', validators=[DataRequired(message='Choose a Language')], choices=languages)
    genre = SelectField(label='Genre', validators=[DataRequired(message='Select a Genre')], choices=genres)
    lyrics = TextAreaField(label='Lyrics')
    submit = SubmitField(label='Update')


class UpdateAlbumForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired(message='Title cannot be empty')])
    tracks = SelectMultipleField(label='Select Tracks', validators=[DataRequired('You must select atleast one track or Upload a new one first')], coerce=int, choices=lambda: [ (track.id, track.title) for track in Track.query.filter_by(creator_id=current_user.id).all()])
    description = TextAreaField(label='Description')
    submit = SubmitField(label='Update')


