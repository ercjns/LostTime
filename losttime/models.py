# losttime/models.py

from . import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    date = db.Column(db.String)
    venue = db.Column(db.String)
    
    def __init__(self, name, date, venue):
        self.name = name
        self.date = date
        self.venue = venue
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
    score = db.Column(db.Float)

    def __init__(self, eventid, classid, sicard, name, bib, clubshort, coursestatus, resultstatus, time):
        self.eventid = eventid
        self.classid = classid
        self.sicard = sicard
        self.name = name
        self.bib = bib
        self.club_shortname = clubshort
        self.coursestatus = coursestatus
        self.resultstatus = resultstatus
        self.time = time
        return