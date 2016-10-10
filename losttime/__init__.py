# losttime/__init__.py

from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

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

@app.route('/')
def home_page():
    return render_template('home/home.html')