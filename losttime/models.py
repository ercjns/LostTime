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