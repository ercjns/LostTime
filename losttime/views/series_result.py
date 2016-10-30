#losttime/views/series_result.py

from flask import Blueprint, url_for, redirect, request, render_template, jsonify
from losttime.models import db, Event, EventClass, PersonResult, EventTeamClass, TeamResult, Series, SeriesClass


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

        series = Series([int(x) for x in request.form.getlist('events[]')])
        db.session.add(series)
        db.session.commit()

        return jsonify(seriesid=series.id), 202

@seriesResult.route('/info/<seriesid>', methods=['GET', 'POST'])
def series_info(seriesid):
    if request.method == 'GET':
        series = Series.query.get(seriesid)
        eventids = [int(x) for x in series.eventids.split(',')] # TODO handle empty case?
        events = Event.query.filter(Event.id.in_(eventids)).all()
        events.sort(key=lambda x: eventids.index(x.id))
        eventclasses = EventClass.query.filter(EventClass.eventid.in_(eventids)).all()

        seriesclasstable = {}
        for ec in eventclasses:
            starterdict = {event.id:False for event in events}
            starterdict.update({'name':ec.name})
            seriesclasstable.setdefault(ec.shortname, starterdict)[ec.eventid] = ec
        seriesclasses = sorted(seriesclasstable.items(), key=lambda x: x[0])

        return render_template('seriesresult/info.html', series=series, events=events, seriesclasses=seriesclasses)

    elif request.method == 'POST':
        formdata = request.get_json(force=True)
        series = Series.query.get(seriesid)
        series.name = str(formdata['name'])
        series.host = str(formdata['host'])
        series.scoremethod = str(formdata['scoremethod'])
        series.scoreeventscount = int(formdata['scoreeventscount'])
        series.scoreeventsneeded = int(formdata['scoreeventsneeded'])
        db.session.add(series)
        db.session.commit()

        # delete seriesClass and seriesResult objects with this seriesid
        SeriesClass.query.filter_by(seriesid=series.id).delete()
        # SeriesResult.query.filter_by(seriesid=series.id).delete()

        for c in formdata['classes']:
            if len(c['eventclasses']) == 0:
                continue
            name, abbr = c['name'].split(')')[0].split('(')
            print(series.id, name.strip(), abbr, series.eventids, c['eventclasses'])
            sc = SeriesClass(series.id, name.strip(), abbr, series.eventids, c['eventclasses'])
            db.session.add(sc)
        db.session.commit()

        #create and calculate the series scores
        #create the pages
        #redirect to the view/download page
        return jsonify(message="not yet"), 501


