#losttime/views/series_result.py

from flask import Blueprint, url_for, redirect, request, render_template, jsonify
from losttime.models import db, Event, EventClass, PersonResult, EventTeamClass, TeamResult, Series, SeriesClass, ClubCode
from _output_templates import SeriesHtmlWriter
from os.path import join


seriesResult = Blueprint("seriesResult", __name__, static_url_path='/download', static_folder='../static/userfiles')

@seriesResult.route('/')
def home():
    return redirect(url_for('seriesResult.select_events'))

@seriesResult.route('/events', methods=['GET', 'POST'])
def select_events():
    if request.method == 'GET':
        current_events = [3, 36, 26, 34, 35, 30]
        events = Event.query.filter((Event.id.in_(current_events)) | (Event.id > 36)).all()
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
        eventteamclasses = EventTeamClass.query.filter(EventTeamClass.eventid.in_(eventids)).all()

        seriesclasstable = {}
        for ec in eventclasses:
            starterdict = {event.id:False for event in events}
            starterdict.update({'name':ec.name})
            seriesclasstable.setdefault(ec.shortname, starterdict)[ec.eventid] = ec
        seriesclasses = sorted(seriesclasstable.items(), key=lambda x: x[0])

        seriesteamclasstable = {}
        for etc in eventteamclasses:
            starterdict = {event.id:False for event in events}
            starterdict.update({'name':etc.name})
            seriesteamclasstable.setdefault(etc.shortname, starterdict)[etc.eventid] = etc
        seriesteamclasses = sorted(seriesteamclasstable.items(), key=lambda x: x[0])

        return render_template('seriesresult/info.html',
                               series=series,
                               events=events,
                               seriesclasses=seriesclasses,
                               seriesteamclasses=seriesteamclasses)

    elif request.method == 'POST':
        formdata = request.get_json(force=True)
        series = Series.query.get(seriesid)
        series.name = str(formdata['name'])
        series.host = str(formdata['host'])
        series.scoremethod = str(formdata['scoremethod'])
        series.scoreeventscount = int(formdata['scoreeventscount'])
        series.scoreeventsneeded = int(formdata['scoreeventsneeded'])
        series.scoretiebreak = str(formdata['scoretiebreak'])
        db.session.add(series)
        db.session.commit()

        # delete seriesClass and seriesResult objects with this seriesid
        SeriesClass.query.filter_by(seriesid=series.id).delete()
        # SeriesResult.query.filter_by(seriesid=series.id).delete()

        for c in formdata['classes']:
            if len(c['eventclasses']) == 0:
                continue
            name, abbr = c['name'].rsplit('(', 1)
            sc = SeriesClass(series.id, name.strip(), abbr.split(')')[0], series.eventids, c['eventclasses'], c['type'])
            db.session.add(sc)
        db.session.commit()

        #create and calculate the series scores
        seriesresults = _calculateSeries(series.id)

        seriesclasses = SeriesClass.query.filter_by(seriesid=series.id).all()
        # scdict = {sc.shortname: sc for sc in seriesclasses}

        clubcodes = {}
        for club in ClubCode.query.all():
            clubcodes.setdefault(club.code, []).append(club)

        writer = SeriesHtmlWriter(series, formdata['output'], seriesclasses, seriesresults, clubcodes)
        doc = writer.seriesResult()
        filename = join(seriesResult.static_folder, 'SeriesResult-{0:03d}.html'.format(int(seriesid)))
        with open(filename, 'w') as f:
            f.write(doc.render())

        return jsonify(seriesid=seriesid), 201

@seriesResult.route('/results/<seriesid>', methods=['GET'])
def series_result(seriesid):
    try:
        fn = 'SeriesResult-{0:03d}.html'.format(int(seriesid))
        filepath = join(seriesResult.static_folder, fn)
        with open(filepath) as f:
            htmldoc = f.read()
    except IOError:
        return "couldn't find that file...", 404
    return render_template('seriesresult/result.html', seriesid=seriesid, thehtml=htmldoc, fn=fn)


def _calculateSeries(seriesid):
    series = Series.query.get(seriesid)
    eventids = [int(x) for x in series.eventids.split(',')]
    seriesclasses = SeriesClass.query.filter_by(seriesid=seriesid).all()
    seriesresults = {}
    for sc in seriesclasses:
        ecids = [int(x) for x in sc.eventclassids.split(',')]
        scresultdict = {}
        if sc.classtype == 'indv':
            results = PersonResult.query.filter(PersonResult.classid.in_(ecids)).all()
            for r in results:
                if r.resultstatus == 'nc':
                    continue
                defaultdict = {'name':r.name, 'club':r.club_shortname, 'results':{x:False for x in eventids}}
                # Key: NAME-CLUBCODE causes issues if club is inconsistent
                # Key: NAME causes issues if people have the same name.
                seriesresultkey = '{0}-{1}'.format(r.name.upper(), r.club_shortname)
                scresultdict.setdefault(seriesresultkey, defaultdict)['results'][r.eventid] = r
        elif sc.classtype == 'team':
            results = TeamResult.query.filter(TeamResult.teamclassid.in_(ecids)).all()
            for r in results:
                defaultdict = {'name':r.teamname_short, 'results':{x:False for x in eventids}}
                scresultdict.setdefault(r.teamname_short, defaultdict)['results'][r.eventid] = r
        else:
            raise "Didn't find any results"

        for sr in scresultdict.values():
            sr['score'], sr['scores'] = _calculateSeriesScore(series, sr['results'].values())

        scresults = _assignSeriesClassPositions(series, [x for x in scresultdict.values() if x['score'] is not None])
        scresults.sort(key=lambda x: x['position'])
        seriesresults[sc.shortname] = scresults
    return seriesresults

def _calculateSeriesScore(series, results):
    results = [x for x in results if (isinstance(x, PersonResult) or isinstance(x, TeamResult)) and (x.score is not None)]
    # TODO: need to detect if good scores are high or low (!)
    results.sort(key=lambda x: -x.score)
    scores = [x.score for x in results[:series.scoreeventscount]]
    # TODO: filter on result status, not just result existance 
    if len(scores) < series.scoreeventsneeded:
        return False, False
    if series.scoremethod == 'sum':
        score = sum(scores)
    elif series.scoremethod == 'average':
        score = float(scores)/len(scores)
    else:
        raise "unknown scoring method"
    if series.scoretiebreak == 'all':
        tiebreakscores = [x.score for x in results]
    elif series.scoretiebreak == 'scoring':
        tiebreakscores = scores
    else:
        tiebreakscores = []
    return score, tiebreakscores


def _assignSeriesClassPositions(series, seriesclassresults):
    # TODO: are good scores high or low (!)
    seriesclassresults.sort(key=lambda x: -x['score'])
    prev = {'pos':0, 'count':1, 'score':0}
    for i in range(len(seriesclassresults)):
        seriesclassresults[i]['position'] = prev['pos'] + prev['count']
        if seriesclassresults[i]['score'] == prev['score']:
            tie = False
            swap = False
            A_scores = seriesclassresults[i-1]['scores'][:]
            B_scores = seriesclassresults[i]['scores'][:]

            while A_scores and B_scores:
                A, B = A_scores.pop(0), B_scores.pop(0)
                if A > B:
                    break
                elif B > A:
                    swap = True
                    break
            else:
                if B == 0 and A == 0:
                    tie = True
                elif B_scores and not A_scores:
                    swap = True
                elif not A_scores and not B_scores:
                    tie = True

            if tie:
                seriesclassresults[i]['position'] = prev['pos']
                prev['count'] += 1
            elif swap:
                seriesclassresults[i]['position'] = seriesclassresults[i-1]['position']
                seriesclassresults[i-1]['position'] = prev['pos'] + prev['count']
                prev['pos'] = seriesclassresults[i-1]['position']
                prev['count'] = 1
            else:
                # tiebreak results in holding current positions
                prev['pos'] = seriesclassresults[i]['position']
                prev['count'] = 1
        else:
            # not tied, update the prev dict.
            prev['pos'] = seriesclassresults[i]['position']
            prev['count'] = 1
            prev['score'] = seriesclassresults[i]['score']
    return seriesclassresults
