#losttime/views/EventResult.py

from flask import Blueprint, url_for, redirect, request, render_template
from datetime import datetime
from losttime import eventfiles
from losttime.models import db, Event, EventClass, PersonResult, EventTeamClass, TeamResult
from _orienteer_data import OrienteerXmlReader
from _output_templates import EventHtmlWriter
from os import remove
from os.path import join


eventResult = Blueprint("eventResult", __name__, static_url_path='/download', static_folder='../static/userfiles')

@eventResult.route('/')
def home():
    return redirect(url_for('eventResult.upload_event'))

@eventResult.route('/upload', methods=['GET', 'POST'])
def upload_event():
    """Load a single event into the database

    Read an xml <ResultList>, create Event, EventClass, and PersonResult entries
    """
    if request.method == 'GET':
        err = request.args.get('e', '')
        return render_template('eventresult/upload.html', error=err)

    elif request.method == 'POST':
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = 'event_'+timestamp+'.'
        try:
            infile = eventfiles.save(request.files['eventfile'], name=filename)
        except:
            # TODO log the failure with the original file name
            # TODO split out handling of different types of exceptions
            # TODO find a better way to pass error string than directly in the url
            return redirect(url_for('eventResult.upload_event', e='Missing or invalid file'))


        reader = OrienteerXmlReader(eventfiles.path(infile))
        if not reader.validiofxml:
            return redirect(url_for('eventResult.upload_event', e='Could not parse xml file'))
        eventdata = reader.getEventMeta()

        new_event = Event(eventdata['name'], eventdata['date'], eventdata['venue'])
        db.session.add(new_event)
        db.session.commit()
        eventid = new_event.id

        for ec in eventdata['classes']:
            new_ec = EventClass(eventid, ec.name, ec.shortname)
            db.session.add(new_ec)
            db.session.commit() # must commit to get id (?)
            classid = new_ec.id

            results = reader.getClassPersonResults(ec.soupCR)
            for pr in results:
                new_pr = PersonResult(eventid, classid, pr.sicard, pr.name, pr.bib, pr.clubshortname, pr.coursestatus, pr.resultstatus, pr.time)
                db.session.add(new_pr)
        db.session.commit()

        remove(eventfiles.path(infile))
        return redirect(url_for('eventResult.event_info', eventid=eventid))

@eventResult.route('/info/<eventid>', methods=['GET', 'POST'])
def event_info(eventid):
    """Manage event information

    Select scoring methods for event classes, edit name, date, venue
    """
    if request.method == 'GET':
        event_data = Event.query.get(eventid)
        classes = EventClass.query.filter_by(eventid=eventid).all()
        return render_template('eventresult/info.html', event=event_data, classes=classes)

    elif request.method == 'POST':
        event = Event.query.get(eventid)
        event.name = request.form['event-name']
        event.date = request.form['event-date']
        event.venue = request.form['event-venue']
        # event.teamscoremethod = request.form['event-team-score-method']
        db.session.add(event)

        classes = EventClass.query.filter_by(eventid=eventid).all()
        for ec in classes:
            form_name = 'class-score-method-{0}'.format(ec.id)
            ec.scoremethod = request.form[form_name]
            db.session.add(ec)
        db.session.commit()

        _assignPositions(eventid)
        _assignScores(eventid)
        _assignTeamScores(eventid, request.form['event-team-score-method'])

        docdict = _buildResultPages(eventid, request.form['output-style'])
        for key,doc in docdict.iteritems():
            filename = join(eventResult.static_folder, 'EventResult-{0:03d}-{1}.html'.format(int(eventid),key))
            with open(filename, 'w') as f:
                f.write(doc.render())

        return redirect(url_for('eventResult.event_results', eventid=eventid))

@eventResult.route('/results/<eventid>', methods=['GET'])
def event_results(eventid):
    """Display formatted page for download

    """
    try:
        indvfn = 'EventResult-{0:03d}-indv.html'.format(int(eventid))
        filepath = join(eventResult.static_folder, indvfn)
        with open(filepath) as f:
            indvhtmldoc = f.read()
    except IOError:
        return "It seems that there are no event results files for event {0}".format(eventid), 404
    try:
        teamfn = 'EventResult-{0:03d}-team.html'.format(int(eventid))
        filepath = join(eventResult.static_folder, teamfn)
        with open(filepath) as f:
            teamhtmldoc = f.read()
    except:
        teamfn = None
        teamhtmldoc = None
    return render_template('eventresult/result.html', eventid=eventid, indvhtml=indvhtmldoc, indvfn=indvfn, teamhtml=teamhtmldoc, teamfn=teamfn)

def _assignPositions(eventid):
    """Assign position to PersonResult.position

    Given an eventid, queries for associated PersonResults, computes and assigns position.
    Ties are awarded the same place, with the following finisher bumped an extra place down.
    For example the first 5 places, including a tie for 2nd, are: 1, 2, 2, 4, 5.
    Positions only assigned for 'time', 'worldcup', and '1000pts' scoremethods, others skipped.
    Invalid results are assigned a place of -1.
    """
    classes = EventClass.query.filter_by(eventid=eventid).all()
    for ec in classes:
        ec_results = PersonResult.query.filter_by(eventid=eventid).filter_by(classid=ec.id).all()
        if len(ec_results) == 0:
            # TODO log event class with no results.
            continue

        if ec.scoremethod in ['time', 'worldcup', '1000pts']:
            ec_results.sort(key=lambda x: x.time)
            prev_result = (0, 1, -1) # (position, results in current position, time)
            for i in range(len(ec_results)):
                if ec_results[i].coursestatus != 'ok' or ec_results[i].resultstatus != 'ok':
                    ec_results[i].position = -1
                    continue
                ec_results[i].position = prev_result[0] + prev_result[1]
                if ec_results[i].time == prev_result[2]:
                    ec_results[i].position = prev_result[0]
                    prev_result = (ec_results[i].position, prev_result[1]+1, ec_results[i].time)
                else:
                    prev_result = (ec_results[i].position, 1, ec_results[i].time)
            db.session.add_all(ec_results)

        elif ec.scoremethod in ['alpha', 'hide']:
            continue
        else:
            # TODO log unknown score method
            continue
    db.session.commit()
    return

def _assignScores(eventid):
    """Assign values to PersonResult.score

    Given an eventid, queries for associated PersonResults, computes and assigns scores.
    PersonResults must already be assigned positions, including correct allocation of ties.
    Recognized scoring methods (read from EventClass.scoremethod) are:
        'worldcup': 100, 95, 92, 90, 89, 88, 87, ...
        '1000pts': round ( (winning time / competitor time) * 1000 )
        'time': duplicates the time to the score column (integer seconds)
        'hide', 'alpha' or '' will skip
        anything else will log a warning and skip
    """
    classes = EventClass.query.filter_by(eventid=eventid).all()
    for ec in classes:
        if ec.scoremethod == 'worldcup':
            results = PersonResult.query.filter_by(eventid=eventid).filter_by(classid=ec.id).all()
            for r in results:
                if not r.position:
                    # TODO log position not assigned
                    continue
                elif (r.position == -1) or (r.position >= 94):
                    r.score = 0
                elif r.position == 1:
                    r.score = 100
                elif r.position == 2:
                    r.score = 95
                elif r.position == 3:
                    r.score = 92
                else:
                    r.score = 100 - 6 - int(r.position)
            db.session.add_all(results)
        elif ec.scoremethod == '1000pts':
            results = PersonResult.query.filter_by(eventid=eventid).filter_by(classid=ec.id).all()
            win_time = next((x.time for x in results if x.position == 1), 0)
            for r in results:
                if r.position > 0:
                    r.score = round((float(win_time) / r.time) * 1000)
                else:
                    r.score = 0
            db.session.add_all(results)
        elif ec.scoremethod == 'time':
            results = PersonResult.query.filter_by(eventid=eventid).filter_by(classid=ec.id).all()
            for r in results:
                if r.position > 0:
                    r.score = r.time
                else:
                    r.score = 0
            db.session.add_all(results)
        elif ec.scoremethod in ['', 'hide', 'alpha']:
            continue
        else:
            # TODO log an unknown score method
            continue
    db.session.commit()
    return

def _assignTeamScores(eventid, scoremethod):
    """Calculate and assign values to TeamResult.score and TeamResult.position

    Individual scores must be assigned before calling this function.
    WIOL:
        create EventTeamClass, create TeamResult with scores
        sort TeamResults, assign Positions, break ties.
    """
    if scoremethod in ['none']:
        return
    elif scoremethod == 'wiol':
        EventTeamClass.query.filter_by(eventid=eventid).delete()
        TeamResult.query.filter_by(eventid=eventid).delete()
        db.session.commit()

        teamclasses = {}
        classes = EventClass.query.filter_by(eventid=eventid).all()
        for ec in classes:
            if (ec.shortname == 'W2F') or (ec.shortname == 'W2M'):
                if teamclasses.has_key('WT2'):
                    teamclasses['WT2'][1].append(ec.id)
                else:
                    teamclasses['WT2'] = ('Middle School Teams', [ec.id])
            elif ec.shortname == 'W3F':
                teamclasses['WT3F'] = ('JV Girls Teams', [ec.id])
            elif ec.shortname == 'W4M':
                teamclasses['WT4M'] = ('JV Boys North Teams', [ec.id])
            elif ec.shortname == 'W5M':
                teamclasses['WT5M'] = ('JV Boys South Teams', [ec.id])
            elif ec.shortname == 'W6F':
                teamclasses['WT6F'] = ('Varsity Girls Teams', [ec.id])
            elif ec.shortname == 'W6M':
                teamclasses['WT6M'] = ('Varsity Boys Teams', [ec.id])
            else:
                pass
        if len(teamclasses.keys()) == 0:
            return
        for k, v in teamclasses.iteritems():
            new_tc = EventTeamClass(eventid, k, v[0], v[1], 'wiol')
            db.session.add(new_tc)
        db.session.commit()

        teamclasses = EventTeamClass.query.filter_by(eventid=eventid).all()
        for tc in teamclasses:
            results = []
            for ec in tc.classids.split(','):
                results += PersonResult.query.filter_by(classid=int(ec)).all()
            teams = set([r.club_shortname for r in results])
            for team in teams:
                members = [r for r in results if r.club_shortname == team]
                members.sort(key=lambda x: x.score, reverse=True)
                members = members[:3]
                memberids = [m.id for m in members]
                teamscore = sum([m.score for m in members])
                new_team = TeamResult(eventid, tc.id, team, memberids, teamscore)
                db.session.add(new_team)
            db.session.commit()

            teamresults = TeamResult.query.filter_by(teamclassid=tc.id).all()
            teamresults.sort(key=lambda x: -x.score)
            prev_result = {'pos':0, 'count':1, 'score':0}
            for i in range(len(teamresults)):
                teamresults[i].position = prev_result['pos'] + prev_result['count']
                if teamresults[i].score == prev_result['score']:
                    pos_tie = False
                    pos_swap = False
                    A_memberids = teamresults[i-1].resultids.split(',')
                    B_memberids = teamresults[i].resultids.split(',')

                    while A_memberids and B_memberids:
                        A_score = PersonResult.query.get(A_memberids.pop(0)).score
                        B_score = PersonResult.query.get(B_memberids.pop(0)).score
                        if A_score > B_score:
                            # A member n beat B member n, team position correct, not tied
                            break
                        elif B_score > A_score:
                            # B member n beat A member n, team positions swap, not tied
                            pos_swap = True
                            break
                        else:
                            continue
                    else:
                        if A_memberids:
                            # A has more members, team position correct, not tied
                            break
                        elif B_memberids:
                            # B has more members, team positions swap, not tied
                            pos_swap = True
                            break
                        else:
                            pos_tie = True

                    if pos_tie:
                        teamresults[i].position = prev_result['pos']
                        prev_result = {'pos': prev_result['pos'],
                                       'count': prev_result['count'] + 1,
                                       'score': teamresults[i].score}
                        continue
                    elif pos_swap:
                        teamresults[i].position = teamresults[i-1].position
                        teamresults[i-1].position = prev_result['pos'] + prev_result['count']
                        prev_result = {'pos': teamresults[i-1].position,
                                       'count': 1,
                                       'score': teamresults[i-1].score}
                        continue
                    else:
                        prev_result = {'pos': teamresults[i].position,
                                       'count': 1,
                                       'score': teamresults[i].score}
                        continue
                else:
                    prev_result = {'pos': teamresults[i].position,
                                   'count': 1,
                                   'score': teamresults[i].score}

            db.session.add_all(teamresults)
        db.session.commit()
        return


def _buildResultPages(eventid, style):
    """Build and save html page of the Results, for download

    """
    event = Event.query.filter_by(id=eventid).one()
    classes = EventClass.query.filter_by(eventid=eventid).filter(EventClass.scoremethod != 'hide').all()
    results = PersonResult.query.filter_by(eventid=eventid).all()
    teamclasses = EventTeamClass.query.filter_by(eventid=eventid).all()
    teamresults = TeamResult.query.filter_by(eventid=eventid).all()
    # TODO carry the style variable through
    writer = EventHtmlWriter(event, classes, results, teamclasses, teamresults)
    docdict = {}
    indvdoc = writer.eventResultIndv()
    if indvdoc is not None:
        docdict['indv'] = indvdoc
    teamdoc = writer.eventResultTeam()
    if teamdoc is not None:
        docdict['team'] = teamdoc
    return docdict
