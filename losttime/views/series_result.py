#losttime/views/series_result.py

from flask import Blueprint, url_for, redirect, request, render_template, jsonify
from losttime.models import db, Event, EventClass, PersonResult, EventTeamClass, TeamResult


seriesResult = Blueprint("seriesResult", __name__, static_url_path='/download', static_folder='../static/userfiles')

@seriesResult.route('/')
def home():
    return redirect(url_for('seriesResult.select_events'))

@seriesResult.route('/events', methods=['GET', 'POST'])
def select_events():
    if request.method == 'GET':
        events = Event.query.all()
        return render_template('seriesresult/events.html', events=events)

    elif request.method == 'POST':
        # if CODE in series Results table, grab that series result
        # request.form.get('code')
        # if CODE blank, or not in series results table
        #    create a new series result, get it.
        # set the events to the events on the page... 
        # myseries.events = request.form.getlist('events[]')
        # redirect to the info page for this series  

        print(request.form.get('code'))
        print(request.form.getlist('events[]'))
        return jsonify(code='GOGOGO'), 501

@seriesResult.route('/info/<seriesid>', methods=['GET', 'POST'])
def series_info(seriesid):
    if request.method == 'GET':
        #grab the seriesid
        #grab the associated events / eventclasses eventteamclasses
        return render_template('seriesresult/info.html')

    elif request.method == 'POST':
        #read the form
        #save the parameters
        #create and calculate the series scores
        #create the pages
        #redirect to the view/download page
        pass

