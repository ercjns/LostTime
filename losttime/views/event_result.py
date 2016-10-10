#losttime/views/EventResult.py

from flask import Blueprint, url_for, redirect, request, render_template

eventResult = Blueprint("eventResult", __name__, static_url_path='/download', static_folder='../static/userfiles')

@eventResult.route('/')
def home():
    return redirect(url_for('eventResult.upload_event'))

@eventResult.route('/upload', methods=['GET', 'POST'])
def upload_event():
    if request.method == 'GET':
        err = request.args.get('e','')
        return render_template('eventresult/upload.html', error=err)

    elif request.method == 'POST':
        pass
    
