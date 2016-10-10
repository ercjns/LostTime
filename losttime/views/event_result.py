#losttime/views/EventResult.py

from flask import Blueprint, url_for, redirect, request, render_template
from datetime import datetime
from losttime import eventfiles
from losttime.models import db, Event, EventClass, PersonResult
from _orienteer_data import OrienteerXmlReader
from os import remove


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
        err = request.args.get('e','')
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
            db.session.commit() # must commit to get id
            classid = new_ec.id

            results = reader.getClassPersonResults(ec.soupCR)
            for pr in results:
                new_pr = PersonResult(eventid, classid, pr.sicard, pr.name, pr.bib, pr.clubshortname, pr.coursestatus, pr.resultstatus, pr.time)
                db.session.add(new_pr)
        db.session.commit()

        remove(eventfiles.path(infile))

        return 'Populated db for event ' + str(eventid)
        
    
