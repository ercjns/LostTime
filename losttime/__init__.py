# losttime/__init__.py

from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_uploads import UploadSet, configure_uploads

from os.path import join

import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, instance_relative_config=True)

app.config.from_object('config')
try:
    app.config.from_pyfile('instanceconfig.py')
except IOError:
    pass

if not app.debug:
    logfilehandler = RotatingFileHandler('logfile.log', maxBytes=10000, backupCount=1)
    app.logger.addHandler(logfilehandler)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

eventfilepath = join('losttime', 'static', 'userfiles')
eventfiles = UploadSet('eventfiles', ('xml',), lambda app:eventfilepath)
entryfilepath = join('losttime', 'static', 'userfiles')
entryfiles = UploadSet('entryfiles', ('csv',), lambda app:entryfilepath)
configure_uploads(app, (eventfiles, entryfiles))

from .views.event_result import eventResult as eventResultBP
app.register_blueprint(eventResultBP, url_prefix='/event-result')

from .views.entry_manager import entryManager as entryManagerBP
app.register_blueprint(entryManagerBP, url_prefix='/entry-manager')

@app.route('/')
def home_page():
    return render_template('home/home.html')

