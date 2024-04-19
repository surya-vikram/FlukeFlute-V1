from FlukeFlute.models import Language, Role, Genre, User
from FlukeFlute import db
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import os

def add_roles():
    roles = ['Admin', 'Basic', 'Creator']
    for role in roles:
        if not Role.query.filter_by(name=role).first():
            db.session.add(Role(name=role))
    db.session.commit()


def add_languages():
    languages = ['English', 'Spanish', 'French', 'German', 'Japanese']
    for lang in languages:
        if not Language.query.filter_by(name=lang).first():
            db.session.add(Language(name=lang))
    db.session.commit()


def add_genres():
    genres = ['Pop', 'Rock', 'Hip Hop', 'Country', 'Electronic']
    for genre in genres:
        if not Genre.query.filter_by(name=genre).first():
            db.session.add(Genre(name=genre))
    db.session.commit()


def create_admin(username, email, password):
    user = User.query.filter_by(username=username).first()
    admin_role = Role.query.filter_by(name='Admin').first()
    if user:
        if admin_role not in user.roles:
            user.roles.append(admin_role)
    else:
        db.session.add(User(username=username, email=email, password=password, roles=[admin_role]))
    db.session.commit()


def pie_chart(xdata, ydata, filename):
    try:
        path = os.path.join('static/images', filename)
        plt.pie(ydata, labels=xdata)
        plt.axis('equal')
        plt.savefig(os.path.join(os.path.abspath(os.path.dirname(__file__)), path))
        plt.clf()
    except Exception:
        pass


def column_chart(xdata, ydata, filename):
    try:
        path = os.path.join('static/images', filename)
        plt.bar(xdata, ydata, width=0.5)
        plt.savefig(os.path.join(os.path.abspath(os.path.dirname(__file__)), path))
        plt.clf()
    except Exception:
        pass
