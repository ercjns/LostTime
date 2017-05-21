#losttime/views/series_result.py

from flask import Blueprint, url_for, redirect, request, render_template, jsonify, flash
from losttime.models import db, Event, EventClass, PersonResult, EventTeamClass, TeamResult, Series, SeriesClass, ClubCode
from _output_templates import SeriesHtmlWriter
from os.path import join
from fuzzywuzzy import fuzz
import itertools, unicodedata


seriesResult = Blueprint("seriesResult", __name__, static_url_path='/download', static_folder='../static/userfiles')

@seriesResult.route('/')
def home():
    return redirect(url_for('seriesResult.select_events'))

@seriesResult.route('/events', methods=['GET', 'POST'])
def select_events():
    if request.method == 'GET':
        # current_events = [3, 36, 26, 34, 35, 30]
        # events = Event.query.filter((Event.id.in_(current_events)) | (Event.id > 36)).all()
        events = Event.query.all()
        return render_template('seriesresult/events.html', events=events)

    elif request.method == 'POST':
        # if CODE in series Results table, grab that series result
        # request.form.get('code')

        series = Series([int(x) for x in request.form.getlist('events[]')])
        db.session.add(series)
        db.session.commit()

        return jsonify(seriesid=series.id), 202

@seriesResult.route('/getEvents', methods=['GET'])
def get_series_events():
    serieskey = request.args.get('serieskey')
    my_series = Series.query.get(serieskey)
    events = my_series.eventids.split(',')
    print(events)
    return jsonify(events), 200

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

        verifyScoringMethods(seriesclasses + seriesteamclasses)

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

        # delete seriesClass objects with this seriesid
        SeriesClass.query.filter_by(seriesid=series.id).delete()

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
            f.write(doc.render().encode('utf-8'))

        return jsonify(seriesid=seriesid), 201

@seriesResult.route('/results/<seriesid>', methods=['GET'])
def series_result(seriesid):
    try:
        fn = 'SeriesResult-{0:03d}.html'.format(int(seriesid))
        filepath = join(seriesResult.static_folder, fn)
        with open(filepath) as f:
            htmldoc = f.read().decode('utf-8')
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
                ascii_name = unicodedata.normalize('NFKD', r.name.upper()).encode('ascii', 'ignore')
                seriesresultkey = '{0}-{1}'.format(ascii_name, r.club_shortname)
                scresultdict.setdefault(seriesresultkey, defaultdict)['results'][r.eventid] = r
        elif sc.classtype == 'team':
            results = TeamResult.query.filter(TeamResult.teamclassid.in_(ecids)).all()
            for r in results:
                defaultdict = {'name':r.teamname_short, 'results':{x:False for x in eventids}}
                scresultdict.setdefault(r.teamname_short, defaultdict)['results'][r.eventid] = r
        else:
            raise "Didn't find any results"

        # Check to see if any entires in scresultdict might need to be combined
        possible_dupes = [(k,v) for k, v in scresultdict.iteritems() if False in scresultdict[k]['results'].values()]

        name_matches = []
        for r1, r2 in itertools.combinations(possible_dupes, 2):
            ratio1 = fuzz.ratio(r1[1]['name'], r2[1]['name'])
            if ratio1 > 70: # needs tuning. 70 to 80 seems about right.
                # print r1[1]['name'], r2[1]['name'], ratio1
                name_matches.append((r1, r2))

        event_matches = []
        for m1, m2 in name_matches:
            attended_same_event = False
            for matcheventkey in m1[1]['results'].keys():
                if m1[1]['results'][matcheventkey] != False and m2[1]['results'][matcheventkey] != False:
                    attended_same_event = True
                    break
            if not attended_same_event:
                event_matches.append((m1, m2))
                flash("Is {0} ({1}) the same person as {2} ({3})?".format(m1[1]['name'], m1[1]['club'], m2[1]['name'], m2[1]['club']))


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
    seriesclassresults.sort(cmp=sortSeriesResults)
    seriesclassresults.reverse()
    nextpos = 1
    tied = 0
    seriesclassresults[0]['position'] = nextpos
    for i in range(1, len(seriesclassresults)):
        if sortSeriesResults(seriesclassresults[i-1], seriesclassresults[i]) != 0:
            # not tied, increment position by 1 plus previous ties
            nextpos += 1
            nextpos += tied
            tied = 0
        else:
            # tied, next gets same pos, increment tied counter
            tied += 1
        seriesclassresults[i]['position'] = nextpos
    return seriesclassresults


def sortSeriesResults(a, b):
    if a['score'] is None or b['score'] is None:
        raise KeyError('missing score value')
    elif a['score'] > b['score']:
        return 1
    elif b['score'] > a['score']:
        return -1
    elif a['score'] == b['score']:
        return sortTiedSeriesResults(a, b)

def sortTiedSeriesResults(a, b):
    a_scores = a['scores'][:]
    b_scores = b['scores'][:]
    while a_scores and b_scores:
        a, b = a_scores.pop(0), b_scores.pop(0)
        if a > b:
            return 1
        elif b > a:
            return -1
        elif a == 0 and b == 0:
            return 0

    if a_scores and not b_scores:
        return 1
    elif b_scores and not a_scores:
        return -1
    else:
        return 0

def verifyScoringMethods(seriesclasslist):
    """Flashes a message if events comprising a series class use
    more than one scoring methond (and probably shouldn't be combined)
    """
    for scid, scinfo in seriesclasslist:
        methods = []
        for eid, ec in scinfo.iteritems():
            if eid == 'name' or not ec:
                continue
            methods.append(ec.scoremethod)
        if len(set(methods)) > 1:
            if set(methods) != set(['1000pts', 'score1000']):
                flash("Events in class {0} use different scoring methods".format(
                    scinfo['name']
                ))
