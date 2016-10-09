# losttime/__init__.py

from flask import Flask
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


@app.route('/')
def hello_world():
    return 'Hello, World!'