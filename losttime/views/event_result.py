#losttime/views/event_result.py

from flask import Blueprint, url_for, redirect, request, render_template, jsonify, flash
import flask_login
from datetime import datetime
from losttime import eventfiles
from losttime.models import db, Event, EventClass, PersonResult, EventTeamClass, TeamResult, ClubCode
from _orienteer_data import OrienteerResultReader
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
        replace = request.args.get('replace')
        if not flask_login.current_user.is_authenticated:
            flash('Not logged in. Your result will not be associated with an account.', 'warning')
        return render_template('eventresult/upload.html', replaceid=replace)

    elif request.method == 'POST':
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = 'eventResult_{0}.'.format(timestamp)
        try:
            # filename ending with '.' applies extension to end
            infile = eventfiles.save(request.files['eventFile'], name=filename)
        except:
            return jsonify(error="Failed to save file, try again later"), 500

        if request.form['event-type'] == 'score':
            isScoreO = True
            event_type = 'score'
        else:
            isScoreO = False
            event_type = 'standard'
        reader = OrienteerResultReader(eventfiles.path(infile), isScoreO)
        if not reader.isValid:
            remove(eventfiles.path(infile))
            return jsonify(error='Could not parse results from that file.'), 422

        Oevent = reader.getEventMeta()
        ltuser = flask_login.current_user.get_id()
        new_event = Event(Oevent.name, Oevent.date, Oevent.venue, None, event_type, ltuser)
        db.session.add(new_event)
        db.session.commit()
        eventid = new_event.id

        for Oec in reader.getEventClasses():
            new_ec = EventClass(eventid, Oec.name, Oec.shortname, Oec.scoremethod)
            db.session.add(new_ec)
            db.session.commit()
            classid = new_ec.id

            for Oepr in reader.getEventClassPersonResults(Oec):
                if isScoreO:
                    ScoreO_data = {'points': Oepr.ScoreO_points, 'penalty': Oepr.ScoreO_penalty}
                else:
                    ScoreO_data = None
                new_pr = PersonResult(
                    eventid,
                    classid,
                    Oepr.sicard,
                    Oepr.name,
                    Oepr.bib,
                    Oepr.clubshortname,
                    Oepr.coursestatus,
                    Oepr.resultstatus,
                    Oepr.time,
                    ScoreO_data
                )
                db.session.add(new_pr)

        db.session.commit()
        remove(eventfiles.path(infile))
        return jsonify(eventid=eventid), 201

@eventResult.route('/info/<eventid>', methods=['GET', 'POST'])
def event_info(eventid):
    """Manage event information

    Select scoring methods for event classes, edit name, date, venue
    """
    if request.method == 'GET':
        replace = Event.query.get(request.args.get('replace'))
        event_data = Event.query.get(eventid)
        classes = EventClass.query.filter_by(eventid=eventid).all()
        return render_template('eventresult/info.html', 
                               event=event_data, 
                               classes=classes,
                               replace=replace)

    elif request.method == 'POST':
        event = Event.query.get(eventid)
        event.name = request.form['event-name']
        try:
            event.date = datetime.strptime(request.form['event-date'], "%Y-%m-%d")
        except:
            event.data = None
        event.venue = request.form['event-venue']
        event.host = request.form['event-host']
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
                f.write(doc.render().encode('utf-8'))

        replace = request.form['replace'] # string id or 'None'
        if replace != 'None':
            replaced = mark_event_as_replaced(replace, event.id)
            if replaced:
                flash('Updated event {} with this event result.'.format(replace), 'info')
            else:
                flash("Didn't update event {}, something went wrong!".format(replace), 'warning')

        # prev = Event.query.get(replace) # Event object or Nonetype
        # if prev != None:
        #     ltuser = flask_login.current_user.get_id()
        #     if (ltuser != None) and (int(ltuser) == prev.ltuserid):
        #         prev.replacedbyid = eventid
        #         db.session.add(prev)
        #         old_events = Event.query.filter_by(replacedbyid=replace).all()
        #         for old_event in old_events:
        #             old_event.replacedbyid = eventid
        #             db.session.add(old_event)
        #         db.session.commit()
        #         flash('Updated event {} with this event result.'.format(prev.name), 'info')
        #     else:
        #         flash("Didn't update event {}, that is not your event!".format(prev.name), 'warning')

        event = Event.query.get(eventid)
        event.isProcessed = True
        db.session.add(event)
        db.session.commit()

        return redirect(url_for('eventResult.event_results', eventid=eventid, replace=replace))


def mark_event_as_replaced(old_event_id, new_event_id):
    if old_event_id == 'None' or new_event_id == 'None':
        return False

    old_event = Event.query.get(old_event_id)
    new_event = Event.query.get(new_event_id)

    ltuser = flask_login.current_user.get_id()
    if (ltuser != None) and (int(ltuser)) == old_event.ltuserid and (int(ltuser)) == new_event.ltuserid:
        old_event.replacedbyid = new_event.id
        db.session.add(old_event)
        older_events = Event.query.filter_by(replacedbyid=old_event_id).all()
        for older_event in older_events:
            older_event.replacedbyid = new_event.id
            db.session.add(older_event)
        db.session.commit()
        return True
    return False


@eventResult.route('/replace', methods=['POST'])
def mark_as_replaced():
    old_event = request.form['old_event']
    new_event = request.form['new_event']
    replaced = mark_event_as_replaced(old_event, new_event)
    if replaced:
        flash('Marked {} as replaced by {}'.format(old_event, new_event), 'info')
    else:
        flash('Something went wrong, no changes made.', 'warning')
    return redirect(url_for('users.user_home')), 200


@eventResult.route('/results/<eventid>', methods=['GET'])
def event_results(eventid):
    """Display formatted page for download

    """
    try:
        indvfn = 'EventResult-{0:03d}-indv.html'.format(int(eventid))
        filepath = join(eventResult.static_folder, indvfn)
        with open(filepath) as f:
            indvhtmldoc = f.read().decode('utf-8')
    except IOError:
        return "It seems that there are no event results files for event {0}".format(eventid), 404
    try:
        teamfn = 'EventResult-{0:03d}-team.html'.format(int(eventid))
        filepath = join(eventResult.static_folder, teamfn)
        with open(filepath) as f:
            teamhtmldoc = f.read().decode('utf-8')
    except:
        teamfn = None
        teamhtmldoc = None
    replaceid = request.args.get('replace')
    return render_template('eventresult/result.html', 
                           eventid=eventid, 
                           indvhtml=indvhtmldoc, 
                           indvfn=indvfn, 
                           teamhtml=teamhtmldoc, 
                           teamfn=teamfn,
                           replaceid=replaceid)

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
        with db.session.no_autoflush:
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
                db.session.commit()
                db.session.flush()

            elif ec.scoremethod in ['score', 'score1000']:
                ec_results.sort(key=lambda x: x.time) #secondary key
                ec_results.sort(key=lambda x: x.ScoreO_net, reverse=True) #primary key
                prev_result = (0, 1, -1, -1) # (position, results in current position, time, score)
                for i in range(len(ec_results)):
                    if ec_results[i].coursestatus != 'ok' or ec_results[i].resultstatus != 'ok':
                        ec_results[i].position = -1
                        continue
                    ec_results[i].position = prev_result[0] + prev_result[1]
                    if ec_results[i].time == prev_result[2] and ec_results[i].ScoreO_net == prev_result[3]:
                        ec_results[i].position = prev_result[0]
                        prev_result = (ec_results[i].position, prev_result[1]+1, ec_results[i].time, ec_results[i].ScoreO_net)
                    else:
                        prev_result = (ec_results[i].position, 1, ec_results[i].time, ec_results[i].ScoreO_net)

            elif ec.scoremethod in ['alpha', 'hide']:
                continue
            else:
                # TODO log unknown score method
                continue
            
    # db.session.commit()
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
                    if r.resultstatus == 'nc':
                        r.score = None
                    else:                   
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
        elif ec.scoremethod == 'score':
            results = PersonResult.query.filter_by(eventid=eventid).filter_by(classid=ec.id).all()
            for r in results:
                if r.position > 0:
                    r.score = r.ScoreO_net
                else:
                    r.score = 0
        elif ec.scoremethod == 'score1000':
            results = PersonResult.query.filter_by(eventid=eventid).filter_by(classid=ec.id).all()
            win_time, win_score = next(((x.time, x.ScoreO_net) for x in results if x.position == 1), 0)
            print(win_time, win_score)
            for r in results:
                if r.ScoreO_net == win_score:
                    r.score = round((float(win_time) / r.time) * 1000)
            slowestSweepScore = min([x.score for x in results if x.score > 0])
            for r in results:
                if r.score != None:
                    continue
                if r.position > 0:
                    r.score = round((r.ScoreO_net / float(win_score)) * slowestSweepScore)
                else:
                    r.score = 0

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
        sum scores for top 3 individuals in each teamclass, hard-coded below
        no minimum number of required finishers for a valid team.
        ties broken by individual scores 1 through 3.
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
                if team in ['None', 'NONE', 'none']:
                    print("not a team: {}".format(team))
                    continue
                members = [r for r in results if (r.club_shortname == team) and (r.resultstatus not in ['nc', 'dns'])]
                numstarts = len(members)
                if numstarts == 0:
                    print("not a team: {}".format(team))
                    continue
                numfinishes = len([x for x in members if x.coursestatus == 'ok'])
                members.sort(key=lambda x: x.score, reverse=True)
                members = members[:3]
                memberids = [m.id for m in members if m.score > 0]
                teamscore = sum([m.score for m in members])
                new_team = TeamResult(eventid, tc.id, team, memberids, teamscore, numstarts, numfinishes)
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
                    if A_memberids == [u'']:
                        A_memberids = []
                    if B_memberids == [u'']:
                        B_memberids = []

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
    """Build and save html page of the event results

    Query the database for all information related to this event id
    Return dict with indivudal results and team results
    """
    event = Event.query.filter_by(id=eventid).one()
    classes = EventClass.query.filter_by(eventid=eventid).filter(EventClass.scoremethod != 'hide').all()
    results = PersonResult.query.filter_by(eventid=eventid).all()
    teamclasses = EventTeamClass.query.filter_by(eventid=eventid).all()
    teamresults = TeamResult.query.filter_by(eventid=eventid).all()
    clubcodes = {}
    for club in ClubCode.query.all():
        clubcodes.setdefault(club.code, []).append(club)

    writer = EventHtmlWriter(event, style, classes, results, teamclasses, teamresults, clubcodes)
    docdict = {}
    docdict['indv'] = writer.eventResultIndv()
    teamdoc = writer.eventResultTeam()
    if teamdoc: # false if no team results page
        docdict['team'] = teamdoc
    return docdict
