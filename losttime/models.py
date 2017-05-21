# losttime/models.py

from . import db
from datetime import datetime

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    date = db.Column(db.DateTime)
    venue = db.Column(db.String)
    host = db.Column(db.String)
    type = db.Column(db.String)
    created = db.Column(db.DateTime)

    def __init__(self, name, date, venue, host, type='standard'):
        self.name = name
        self.date = date
        self.venue = venue
        self.host = host
        self.type = type
        self.created = datetime.now()
        return

class EventClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventid = db.Column(db.Integer)
    name = db.Column(db.String)
    shortname = db.Column(db.String)
    scoremethod = db.Column(db.String)

    def __init__(self, event, name, shortname, scoremethod='time'):
        self.eventid = int(event)
        self.name = name
        self.shortname = shortname
        self.scoremethod = scoremethod
        return

class PersonResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventid = db.Column(db.Integer)
    classid = db.Column(db.Integer)
    sicard = db.Column(db.Integer)
    name = db.Column(db.String)
    bib = db.Column(db.String)
    club_shortname = db.Column(db.String)
    coursestatus = db.Column(db.String) # OK, DNF, MSP
    resultstatus = db.Column(db.String) # OK, DSQ, NC
    time = db.Column(db.Integer)
    position = db.Column(db.Integer)
    ScoreO_points = db.Column(db.Integer) #ScoreO points
    ScoreO_penalty = db.Column(db.Integer) #ScoreO points penalty
    ScoreO_net = db.Column(db.Integer) #ScoreO final score
    score = db.Column(db.Float) #Season / carried score

    def __init__(self, eventid, classid, sicard, name, bib, clubshort, coursestatus, resultstatus, time, scoreO=None):
        self.eventid = eventid
        self.classid = classid
        self.sicard = sicard
        self.name = name
        self.bib = bib
        self.club_shortname = clubshort
        self.coursestatus = coursestatus
        self.resultstatus = resultstatus
        self.time = time
        if scoreO != None:
            self.ScoreO_points = scoreO['points']
            self.ScoreO_penalty = scoreO['penalty']
            self.ScoreO_net = self.ScoreO_points - self.ScoreO_penalty
            if self.ScoreO_net < 0:
                self.ScoreO_net = 0
        return

    def timetommmss(self):
        if (self.time == None) or (self.time == -1):
            return '--:--'
        minutes, seconds = divmod(self.time, 60)
        return '{0:d}:{1:02d}'.format(minutes, seconds)

class EventTeamClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventid = db.Column(db.Integer)
    shortname = db.Column(db.String)
    name = db.Column(db.String)
    classids = db.Column(db.String)
    scoremethod = db.Column(db.String)

    def __init__(self, event, shortname, name, classes, scoremethod=''):
        self.eventid = int(event)
        self.shortname = shortname
        self.name = name
        self.classids = str(classes).strip('[]').replace(' ', '')
        self.scoremethod = scoremethod
        return

class TeamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventid = db.Column(db.Integer)
    teamclassid = db.Column(db.Integer)
    teamname_short = db.Column(db.String)
    position = db.Column(db.Integer)
    score = db.Column(db.Float)
    resultids = db.Column(db.String)
    numstarts = db.Column(db.Integer)
    numfinishes = db.Column(db.Integer)

    def __init__(self, event, teamclass, teamname_short, members, score=None, starts=None, finishes=None):
        self.eventid = event
        self.teamclassid = teamclass
        self.teamname_short = teamname_short
        self.resultids = str(members).strip('[]').replace(' ', '')
        self.score = score
        self.numstarts = starts
        self.numfinishes = finishes
        return

class ClubCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    namespace = db.Column(db.String)
    code = db.Column(db.String)
    name = db.Column(db.String)

    def __init__(self, namespace, code, name):
        self.namespace = namespace
        self.code = code
        self.name = name
        return

class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    host = db.Column(db.String)
    updated = db.Column(db.DateTime)
    eventids = db.Column(db.String)
    scoremethod = db.Column(db.String)
    scoreeventscount = db.Column(db.Integer)
    scoreeventsneeded = db.Column(db.Integer)
    scoretiebreak = db.Column(db.String)

    def __init__(self, events):
        self.eventids = str(events).strip('[]').replace(' ', '')
        return

class SeriesClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seriesid = db.Column(db.Integer)
    name = db.Column(db.String)
    shortname = db.Column(db.String)
    eventids = db.Column(db.String)
    eventclassids = db.Column(db.String)
    classtype = db.Column(db.String)

    def __init__(self, seriesid, name, shortname, eventids, classids, classtype):
        self.seriesid = seriesid
        self.name = name
        self.shortname = shortname
        self.eventids = eventids
        self.eventclassids = str(classids).strip('[]').replace(' ', '')
        self.classtype = classtype
        return
