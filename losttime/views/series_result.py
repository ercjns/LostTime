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
        series.scoretiebreak = str(formdata['scoretiebreak'])
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
        seriesresults = _calculateSeries(series.id)

        # for sc, src in seriesresults.iteritems():
        #     for k, sr in src.iteritems():
        #         print(sc, sr['name'], sr['position'], sr['score'], sr['scores'])
        
        # create the pages
        # return success to front-end, trigger redirect to view/download page
        return jsonify(message="not yet"), 501


def _calculateSeries(seriesid):
    series = Series.query.get(seriesid)
    eventids = [int(x) for x in series.eventids.split(',')]
    seriesclasses = SeriesClass.query.filter_by(seriesid=seriesid).all()
    seriesresults = {}
    for sc in seriesclasses:
        ecids = [int(x) for x in sc.eventclassids.split(',')]
        results = PersonResult.query.filter(PersonResult.classid.in_(ecids)).all()
        if len(results) == 0:
            results = TeamResult.query.filter(TeamResult.teamclassid.in_(ecids)).all()
            if len(results) == 0:
                raise "Didn't find any results"
        scresultdict = {}
        for r in results:
            defaultdict = {'name':r.name, 'club':r.club_shortname, 'results':{x:False for x in eventids}}
            # Key: NAME-CLUBCODE causes issues if club is inconsistent
            # Key: NAME causes issues if people have the same name.
            seriesresultkey = '{0}-{1}'.format(r.name.upper(), r.club_shortname)
            scresultdict.setdefault(seriesresultkey, defaultdict)['results'][r.eventid] = r

        for sr in scresultdict.values():
            sr['score'], sr['scores'] = _calculateSeriesScore(series, sr['results'].values())
        _assignSeriesPositions(series, scresultdict)
        seriesresults[sc.shortname] = scresultdict
    return seriesresults

def _calculateSeriesScore(series, results):
    # TODO: also need to remove result status = NC here.
    results = [x for x in results if isinstance(x, PersonResult) or isinstance(x, TeamResult)]
    # TODO: need to detect if good scores are high or low (!)
    results.sort(key=lambda x: -x.score)
    scores = [x.score for x in results[:series.scoreeventscount]]
    if len(scores) < series.scoreeventsneeded:
        return False
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
    # TODO: also return the list of scores to be used for tiebreaking ("all", "scoring", "tie")
    return score, tiebreakscores


def _assignSeriesPositions(series, seriesresultdict):
    # TODO: are good scores high or low (!)
    seriesresults = seriesresultdict.items()
    seriesresults.sort(key=lambda x: -x[1]['score'])
    prev = {'pos':0, 'count':1, 'score':0}
    # ordered, assign positions to seriesresultdict[k]['position'] = pos
    for i in range(len(seriesresults)):
        k = seriesresults[i][0]
        seriesresultdict[k]['position'] = prev['pos'] + prev['count']
        if seriesresultdict[k]['score'] == prev['score']:
            tie = False
            swap = False
            A_scores = seriesresultdict[seriesresults[i-1][0]]['scores']
            B_scores = seriesresultdict[k]['scores']

            while A_scores and B_scores:
                A, B = A_scores.pop(0), B_scores.pop(0)
                if A > B:
                    break
                elif B > A:
                    swap = True
                    break
            else:
                if A_scores:
                    break
                elif B_scores:
                    swap = True
                    break
                else:
                    tie = True

            if tie:
                seriesresultdict[k]['position'] = prev['pos']
                prev['count'] += 1
            elif swap:
                seriesresultdict[k]['position'] = seriesresultdict[seriesresults[i-1][0]]['position']
                seriesresultdict[seriesresults[i-1][0]]['position'] = prev['pos'] + prev['count']
                prev['pos'] = seriesresultdict[seriesresults[i-1][0]]['position']
                prev['count'] = 1
            else:
                prev['pos'] = seriesresultdict[k]['position']
                prev['count'] = 1
        else:
            prev['pos'] = seriesresultdict[k]['position']
            prev['count'] = 1
            prev['score'] = seriesresultdict[k]['score']
    return
