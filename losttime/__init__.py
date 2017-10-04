# losttime/__init__.py

from flask import Flask
from flask import abort, render_template

from os.path import join
from functools import wraps

app = Flask(__name__, instance_relative_config=True)

### Load external configuration

app.config.from_object('config')
try:
    app.config.from_pyfile('instanceconfig.py')
except IOError:
    pass

### Force SSL

from flask_sslify import SSLify
sslify = SSLify(app)

### Setup the logger

import logging
from logging.handlers import RotatingFileHandler
if not app.debug:
    logfilehandler = RotatingFileHandler('logfile.log', maxBytes=10000, backupCount=1)
    app.logger.addHandler(logfilehandler)

### Initialize the database

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

### Setup Authentication
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

from models import User

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = u"You'll need to login to access that page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)

def requires_mod(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.isMod:
            return abort(403)
        return f(*args, **kwargs)
    return wrapped

### email verification tokens

from itsdangerous import URLSafeTimedSerializer
tokenTimedSerializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

### Setup File Uploads and Upload Paths

from flask_uploads import UploadSet, configure_uploads
eventfilepath = join('losttime', 'static', 'userfiles')
eventfiles = UploadSet('eventfiles', ('xml', 'csv'), lambda app:eventfilepath)
entryfilepath = join('losttime', 'static', 'userfiles')
entryfiles = UploadSet('entryfiles', ('csv',), lambda app:entryfilepath)
configure_uploads(app, (eventfiles, entryfiles))

### TODO:What is this?

@app.template_filter()
def datetimeformat(value, format='%Y-%m-%dT%H:%M:%S'):
    return value.strftime(format)

### Load the Blueprints / Paths

from .views.event_result import eventResult as eventResultBP
app.register_blueprint(eventResultBP, url_prefix='/event-result')

from .views.entry_manager import entryManager as entryManagerBP
app.register_blueprint(entryManagerBP, url_prefix='/entry-manager')

from .views.series_result import seriesResult as seriesResultBP
app.register_blueprint(seriesResultBP, url_prefix='/series-result')

from .views.auth import auth as authBP
app.register_blueprint(authBP)

from .views.users import users as usersBP
app.register_blueprint(usersBP)

from .views.admin import admin as adminBP
app.register_blueprint(adminBP, url_prefix='/admin')

### Homepage

@app.route('/')
def home_page():
    return render_template('home/home.html')
