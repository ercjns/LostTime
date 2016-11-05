#!/bin/sh
echo 'Activating python virtualenv'
. venv/bin/activate
echo 'creating or updating the db'
export FLASK_APP=losttime
python -m flask db upgrade
echo 'Starting the app server'
/home/protected/venv/bin/gunicorn --log-file gunicorn.log --log-level info -p app.pid losttime:app
