#losttime/views/EventResult.py

from flask import Blueprint, url_for, redirect, request, render_template
from datetime import datetime
from losttime import eventfiles
from _orienteer_data import OrienteerXmlReader

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

        return 'Got the event!'
        
    
