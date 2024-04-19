import os
from FlukeFlute import app, db
from FlukeFlute.forms import *
from FlukeFlute.models import *
from werkzeug.utils import secure_filename
from FlukeFlute.utils import pie_chart, column_chart
from flask_login import current_user, login_user, logout_user
from flask import render_template, redirect, url_for, flash, request
from flask_principal import Identity, identity_changed, Permission, RoleNeed, identity_loaded


admin_permission = Permission(RoleNeed('Admin'))
basic_permission = Permission(RoleNeed('Basic'))
creator_permission = Permission(RoleNeed('Creator'))


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    if current_user.is_authenticated:
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))


@app.route('/')
def welcome_page():
    return render_template('base.html', title='Welcome')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(name=form.name.data, username=form.username.data, email=form.email_address.data, password=form.password1.data, roles=[Role.query.filter_by(name='Basic').first()])
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        identity_changed.send(app, identity=Identity(current_user.id))
        flash(f"Account created successfully! You are now logged in as {current_user.username}", category='success')
        return redirect(url_for('home_page'))
    if form.errors:  
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')
    return render_template('register.html', form=form, title='Registration')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            identity_changed.send(app, identity=Identity(current_user.id))
            flash(f'Success! You are logged in as: {current_user.username}', category='success')
            return redirect(url_for('home_page'))
        else:
            flash('Username and password does not match! Please try again',category='danger')
    if form.errors:
        for err_msg in form.errors.values():
            flash(
                f'There was an error in login: {err_msg}', category='danger')
    return render_template('login.html', form=form, title='Login', user='User')


@app.route('/logout')
def logout_page():
    if current_user.is_authenticated:
        logout_user()
        flash('You have been logged out!', category='info')
    return redirect(url_for('welcome_page'))


@app.route('/home', methods=['GET', 'POST'])
@basic_permission.require(http_exception=403)
def home_page():
    searched = None
    artists = User.query.filter_by(is_flagged=False).filter(User.stage_name.isnot(None)).all()
    albums = Album.query.all()
    albums = [ alb for alb in albums if User.query.get(alb.creator_id).is_flagged == False ]
    tracks = [trk for trk in Track.query.all() if User.query.get(trk.creator_id).is_flagged == False]
    if request.method == 'POST':
        searched = request.form.get('searched')
        artists = User.query.filter(User.stage_name.contains(searched)).all()
        tracks = Track.query.filter(Track.title.contains(searched) | Track.lyrics.contains(searched)).all()
        albums = Album.query.filter( Album.title.contains(searched) |Album.description.contains(searched)).all()  
    return render_template('home.html', title='Home', artists=artists, albums=albums, languages=Language.query.all(), genres=Genre.query.all(), searched=searched, tracks=tracks, User=User, Genre=Genre)


@app.route('/trending')
@basic_permission.require(http_exception=403)
def trending_page():
    return render_template('tracks.html',title='Trending Tracks', tracks=Track.trending(), heading='Trending', User=User, Genre=Genre, Track=Track)


@app.route('/top/rated')
@basic_permission.require(http_exception=403)
def top_rated_page():
    return render_template('tracks.html', title='Top Rated Tracks', tracks=Track.top_rated(), heading='Top Rated', User=User, Genre=Genre, Track=Track)


@app.route('/genre/<int:id>')
@basic_permission.require(http_exception=403)
def genre_page(id):
    genre = Genre.query.get(id)
    return render_template('tracks.html',title='Genre-Tracks', tracks=genre.tracks, heading=genre.name, User=User, Genre=Genre, Track=Track)


@app.route('/language/<int:id>')
@basic_permission.require(http_exception=403)
def language_page(id):
    lang = Language.query.get(id)
    return render_template('tracks.html',title='Language-Tracks', tracks=lang.tracks, heading=lang.name, User=User, Genre=Genre, Track=Track)


@app.route('/album/<int:id>')
@basic_permission.require(http_exception=403)
def album_page(id):
    album = Album.query.get(id)
    return render_template('tracks.html', title='Album-Tracks', tracks=album.tracks, heading=album.title, User=User, Genre=Genre, Track=Track)


@app.route('/artist/<int:id>')
@basic_permission.require(http_exception=403)
def artist_page(id):
    artist = User.query.get(id)
    return render_template('tracks.html', title='Artist-Tracks', tracks=artist.tracks, heading=artist.stage_name, User=User, Genre=Genre, Track=Track)


@app.route('/track/<int:id>')
@basic_permission.require(http_exception=403)
def play_page(id):
    track = Track.query.get(id)
    track.increment_playback()
    return render_template('music_player.html', title='Play Music', track=track, Language=Language, User=User, Genre=Genre, Track=Track)


@app.route('/rating/<int:id>/<int:value>')
@basic_permission.require(http_exception=403)
def rate_song(id, value):
    db.session.add(Rating(user_id=current_user.id,track_id=id,rating_value=value))
    db.session.commit()
    flash(f'You have rated track {Track.query.get(id).title} successfully!', category='success')
    return redirect(url_for('play_page', id=id))


@app.route('/playlist')
@basic_permission.require(http_exception=403)
def playlist_page():
    return render_template('playlist.html', title='Playlists', playlists=Playlist.query.all())


@app.route('/playlist/<int:id>')
@basic_permission.require(http_exception=403)
def playlist_tracks(id):
    playlist = Playlist.query.get(id)
    return render_template('tracks.html', title='Playlist-Tracks', tracks=playlist.tracks, heading=playlist.name, User=User, Genre=Genre, Track=Track)


@app.route('/create/playlist', methods=['GET', 'POST'])
@basic_permission.require(http_exception=403)
def create_playlist_page():
    form = CreatePlaylistForm()
    if form.validate_on_submit():
        tracks = [Track.query.get(int(track_id)) for track_id in form.tracks.data]
        playlist = Playlist(name=form.name.data, creator_id=current_user.id, tracks=tracks)
        db.session.add(playlist)
        db.session.commit()
        flash('Playlist created successfully!', category='success')
        return redirect(url_for('playlist_page'))
    if form.errors:
        for err_msg in form.errors.values():
            flash(
                f'There was an error in creating playlist: {err_msg}', category='danger')
    return render_template('create_playlist.html', title='Create Playlist', form=form)


@app.route('/playlist/edit/<int:id>', methods=['GET', 'POST'])
@basic_permission.require(http_exception=403)
def edit_playlist(id):
    playlist = Playlist.query.get(id)
    form = CreatePlaylistForm()
    if form.validate_on_submit():
        playlist.name = form.name.data
        playlist.tracks = [Track.query.get(int(track_id)) for track_id in form.tracks.data]
        db.session.commit()
        flash('Playlist updated successfully!', category='success')
        return redirect(url_for('playlist_page'))
    if form.errors:
        for err_msg in form.errors.values():
            flash(
                f'There was an error in editing the playlist: {err_msg}', category='danger')
    form.name.data = playlist.name
    form.tracks.data = [track.id for track in playlist.tracks]
    return render_template('create_playlist.html', title='Edit Playlist', form=form, playlist=playlist)


@app.route('/playlist/delete/<int:id>', methods=['GET', 'POST'])
@basic_permission.require(http_exception=403)
def delete_playlist(id):
    playlist = Playlist.query.get(id)
    if request.method == 'POST':
        db.session.delete(playlist)
        db.session.commit()
        flash(
            f'Playlist has been deleted successfully!', 'success')
        return redirect(url_for('playlist_page'))
    return render_template('delete_confirmation.html')


@app.route('/profile')
@basic_permission.require(http_exception=403)
def profile_page():
    return render_template('profile.html', current_user=current_user)

 
# Creator Pages


@app.route('/register/creator', methods=['GET', 'POST'])
@basic_permission.require(http_exception=403)
def register_creator_page():
    creator_role = Role.query.filter_by(name='Creator').first()
    if creator_role not in current_user.roles:
        form = CreatorForm()
        if form.validate_on_submit():
            file = form.pfp.data
            pfp_path = os.path.join('static/images', secure_filename(file.filename))
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), pfp_path))
            current_user.make_creator(stage_name=form.stage_name.data, bio=form.bio.data, pfp=secure_filename(form.pfp.data.filename))
            identity_changed.send(app, identity=Identity(current_user.id))
            flash(f"Account created successfully! You are now logged in as {current_user.stage_name}", category='success')
            return redirect(url_for('creator_page'))
        if form.errors:
            for err_msg in form.errors.values():
                flash(f'There was an error in registering you for Creator: {err_msg}', category='danger')
        return render_template('register_creator.html', form=form, title='Creator Sign up')
    return redirect(url_for('creator_page'))


@app.route('/creator')
@creator_permission.require(http_exception=403)
def creator_page():
    return render_template('creator.html', title='Creator Page', albums=Album.query.filter_by(creator_id=current_user.id).all(), tracks = Track.query.filter_by(creator_id=current_user.id).all())


@app.route('/upload/song', methods=['GET', 'POST'])
@creator_permission.require(http_exception=403)
def upload_song_page():
    form = SongUploadForm()
    if form.validate_on_submit():
        file = form.audio.data
        audio_path = os.path.join('static/audios', secure_filename(file.filename))
        form.audio.data.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), audio_path))
        track = Track(title=form.title.data, genre_id=form.genre.data, lyrics=form.lyrics.data, audio_path=secure_filename(file.filename), creator_id=current_user.id, language_id=form.language.data)
        db.session.add(track)
        db.session.commit()
        flash('Song uploaded successfully!', category='success')
        return redirect(url_for('creator_page'))
    if form.errors:
        for err_msg in form.errors.values():
            flash(
                f'There was an error while uploading song: {err_msg}', category='danger')
    return render_template('upload_song.html',heading='Upload Track', title='Upload Track', form=form, languages=Language.query.all(), genres=Genre.query.all())


@app.route('/edit/song/<int:id>', methods=['GET', 'POST'])
@creator_permission.require(http_exception=403)
def edit_track(id):
    track = Track.query.get(id)
    form = UpdateTrackForm(obj=track)
    if form.validate_on_submit():
        track.title = form.title.data
        track.genre_id = form.genre.data
        track.lyrics = form.lyrics.data
        track.language_id = form.language.data
        db.session.commit()
        flash('Song updated successfully!', category='success')
        return redirect(url_for('creator_page'))
    if form.errors:
        for err_msg in form.errors.values():
            flash(
                f'There was an error while uploading song: {err_msg}', category='danger')
    return render_template('upload_song.html',heading='Update Track', title='Update Track', form=form, languages=Language.query.all(), genres=Genre.query.all())


@app.route('/track/delete/<int:id>', methods=['GET', 'POST'])
@creator_permission.require(http_exception=403)
def delete_track(id):
    track = Track.query.get(id)
    if request.method == 'POST':
        db.session.delete(track)
        db.session.commit()
        flash(
            f'Track has been deleted successfully!', 'success')
        return redirect(url_for('creator_page'))
    return render_template('delete_confirmation.html')


@app.route('/album/create', methods=['GET', 'POST'])
@creator_permission.require(http_exception=403)
def create_album_page():
    form = CreateAlbumForm()
    if form.validate_on_submit():
        tracks = [ Track.query.get(int(track_id)) for track_id in form.tracks.data ]
        cover_path = os.path.join('static/images', secure_filename(form.cover.data.filename))
        form.cover.data.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), cover_path))
        album = Album(title=form.title.data, description=form.description.data, cover_path=secure_filename(form.cover.data.filename), creator_id=current_user.id, tracks=tracks)
        db.session.add(album)
        db.session.commit()
        flash('Album created successfully!', category='success')
        return redirect(url_for('creator_page'))
    if form.errors:
        for err_msg in form.errors.values():
            flash(f'There was an error in creating album: {err_msg}', category='danger')
    return render_template('create_album.html', title='Create Album', form=form, heading='Create Album')


@app.route('/album/edit/<int:id>', methods=['GET', 'POST'])
@creator_permission.require(http_exception=403)
def edit_album(id):
    album = Album.query.get(id)
    form = UpdateAlbumForm()
    if form.validate_on_submit():
        album.tracks = [ Track.query.get(int(track_id)) for track_id in form.tracks.data]
        album.title = form.title.data
        album.description = form.description.data
        db.session.commit()
        flash('Album updated successfully!', category='success')
        return redirect(url_for('creator_page'))
    if form.errors:
        for err_msg in form.errors.values():
            flash(f'There was an error in editing album: {err_msg}', category='danger')
    form.title.data = album.title
    form.description.data = album.description
    form.tracks.data = [ trk.id for trk in album.tracks]
    return render_template('create_album.html', title='Update Album', form=form, heading='Update Album')


@app.route('/album/delete/<int:id>', methods=['GET', 'POST'])
@creator_permission.require(http_exception=403)
def delete_album(id):
    album = Album.query.get(id)
    if request.method == 'POST':
        db.session.delete(album)
        db.session.commit()
        flash(
            f'Album has been deleted successfully!', category='success')
        return redirect(url_for('creator_page'))
    return render_template('delete_confirmation.html')


# Admin Pages


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            identity_changed.send(app, identity=Identity(current_user.id))
            flash(f'Success! You are logged in as: {current_user.username}', category='success')
            return redirect(url_for('admin_page'))
        else:
            flash('Username and password does not match! Please try again', category='danger')
    if form.errors:
        for err_msg in form.errors.values():
            flash(
                f'Are you sure you are an admin: {err_msg}', category='danger')
    return render_template('login.html', form=form, title='Login', user='Admin')


@app.route('/admin')
@admin_permission.require(http_exception=403)
def admin_page():
    users = User.query.filter(User.stage_name.is_(None)).count()
    creators = User.query.filter(User.stage_name.isnot(None)).count()
    ratings = [ rating.rating_value for rating in Rating.query.all() ]
    genres = [(genre.name, len(genre.tracks)) for genre in Genre.query.all()]
    languages = [(lang.name, len(lang.tracks)) for lang in Language.query.all()]
    tracks = Track.query.count()
    albums = Album.query.count()
    playlists = Playlist.query.count()
    column_chart(['Tracks','Albums','Playlists'], [tracks, albums, playlists],'taps_chart.png')
    column_chart([i for i in range(1,6)], [ ratings.count(i) for i in range(1,6)], 'ratings_chart.png')
    pie_chart(['Users', 'Creators'], [users, creators], 'ucs_chart.png')
    pie_chart([genre[0] for genre in genres], [genre[1] for genre in genres], 'genres_chart.png')
    pie_chart([language[0] for language in languages], [language[1]  for language in languages], 'languages_chart.png')
    return render_template('admin.html', albums=albums, tracks=tracks, playlists=playlists, users=users, creators=creators)


@app.route('/manage/creators')
@admin_permission.require(http_exception=403)
def manage_creators():
    creators = User.query.filter(User.stage_name.isnot(None)).all()
    return render_template('manage_creators.html', creators=creators)


@app.route('/manage/tracks')
@admin_permission.require(http_exception=403)
def manage_tracks():
    return render_template('manage_tracks.html', tracks=Track.query.all(), User=User)


@app.route('/remove/track/<int:id>', methods=['GET', 'POST'])
@admin_permission.require(http_exception=403)
def remove_track(id):
    track = Track.query.get(id)
    if request.method == 'POST':
        db.session.delete(track)
        db.session.commit()
        return redirect(url_for('manage_tracks'))
    return render_template('admin_delconf.html')


@app.route('/flag/creator/<int:id>')
@admin_permission.require(http_exception=403)
def flag_creator(id):
    creator = User.query.get(id)
    creator.is_flagged = not creator.is_flagged
    db.session.commit()
    return redirect(url_for('manage_creators'))


@app.route('/genre/add', methods=['GET','POST'])
@admin_permission.require(http_exception=403)
def add_new_genre():
    form = AddGenreForm()
    if form.validate_on_submit():
        name = (form.name.data).title()
        genre = Genre.query.filter(Genre.name.ilike(f'%{name}%')).first()
        if not genre:
            db.session.add(Genre(name=name))
            db.session.commit()
        flash('Genre added successfully!', category='success')
        return redirect(url_for('admin_page'))
    if form.errors:
        for err_msg in form.errors.values():
            flash(
                f'There was an error in adding Genre: {err_msg}', category='danger')
    return render_template('add_genre.html', title='Add Genre', form=form)


@app.route('/language/add', methods=['GET','POST'])
@admin_permission.require(http_exception=403)
def add_new_language():
    form =AddLangugeForm()
    if form.validate_on_submit():
        name = (form.name.data).title()
        lang = Language.query.filter(Language.name.ilike(f'%{name}%')).first()
        if not lang:
            db.session.add(Language(name=name))
            db.session.commit()
        flash('Language added successfully!', category='success')
        return redirect(url_for('admin_page'))
    if form.errors:
        for err_msg in form.errors.values():
            flash(f'There was an error in adding Language: {err_msg}', category='danger')
    return render_template('add_language.html', title='Add Language', form=form)


# Error Pages


@app.errorhandler(403)
def access_denied_error(error):
    return render_template('error.html', error_code=403, error_message="You don't have permission to access this page", title='Error403', current_user=current_user, Role=Role), 403

@app.errorhandler(404)
def page_not_found_error(error):
    return render_template('error.html', error_code=404, error_message="The requested page doesn't exist", title='Error404', current_user=current_user,Role=Role), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', error_code=500, error_message="Internal Server Error", title='Error500', current_user=current_user, Role=Role), 500
    
    
