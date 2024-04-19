from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_principal import Principal

app = Flask(__name__)

app.config['SECRET_KEY'] = '5155751ad9cfeb61ecda677b087e0a37'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///FlukeFluteDB.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
principal = Principal(app)

login_manager.login_view = 'login_page'
login_manager.login_message_category = 'info'  

app.app_context().push()

from FlukeFlute import views

