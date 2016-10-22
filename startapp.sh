#!/bin/sh
echo 'Activating python virtualenv'
source venv/bin/activate
echo 'Starting the app server'
/home/protected/venv/bin/gunicorn --log-file gunicorn.log --log-level info -p app.pid losttime:app
