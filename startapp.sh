#!/bin/sh
echo 'Entering the virtualenvironment losttime'
workon losttime
echo 'Starting the app server'
gunicorn losttime:app -p app.pid