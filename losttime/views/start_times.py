#losttime/views/start_times.py

from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from datetime import datetime
from losttime import startsfiles
import re
from os import remove
from os.path import join, isfile
from _WiolStartAssignment import Event

startTimes = Blueprint("startTimes", __name__, static_url_path='/download', static_folder='../static/userfiles')

@startTimes.route('/')
def home():
    return redirect(url_for('startTimes.upload_registrations'))

@startTimes.route('/upload', methods=['GET', 'POST'])
def upload_registrations():
    """
    """
    if request.method == 'GET':
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return render_template('starttimes/upload.html', stamp=timestamp)

    elif request.method == 'POST':
        file = request.files['startsFile']
        fn = startsfiles.save(file, name='WiolRegistrations_{0}.csv'.format(request.form['stamp']))
        e = Event()
        # e.add_courses(join(startTimes.static_folder, 'WiolCourseTimes.csv')) #../static/userfiles/WiolCourseTimes.csv
        # e.add_courses(url_for('static', filename=join('adminfiles', 'WiolCourseTimes.csv'))) #/static/adminfiles/WiolCourseTimes.csv
        e.add_courses('losttime/static/adminfiles/WiolCourseTimes.csv')
        e.create_registrations(startsfiles.path(fn))
        e.assign_starts()
        outfilename = join(startTimes.static_folder, 'StartTimes-{0}.csv'.format(request.form['stamp']))
        e.export_start_list(outfilename)
        remove(startsfiles.path(fn))
        return jsonify(stamp=request.form['stamp']), 201

@startTimes.route('/starts/<startsid>', methods=['GET'])
def download_starts(startsid):
    """
    """
    startsfn = 'StartTimes-{0}.csv'.format(startsid)
    if isfile(join(startTimes.static_folder, startsfn)):
        return render_template('starttimes/download.html', startsfn=startsfn, stats=None)

    return("Hmm... we didn't find that file"), 404