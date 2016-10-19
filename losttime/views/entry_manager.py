#losttime/views/entry_manager.py

from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from datetime import datetime

entryManager = Blueprint("entryManager", __name__, static_url_path='/download', static_folder='static/userfiles')

@entryManager.route('/')
def home():
    return redirect(url_for('entryManager.upload_entries'))

@entryManager.route('/upload', methods=['GET', 'POST'])
def upload_entries():
    """Allow for users to upload entry files, process uploads

    reads csv or xml data and creates the same ready for import to OE or other event managers.
    """
    if request.method == 'GET':
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return render_template('entrymanager/upload.html', stamp = timestamp)

    elif request.method == 'POST':
        print('Got these files: ', request.files)
        # recieve files from dropzone, ok to take them one at a time
        # process the file on upload, create the output, associate it with the timestamp
        # save the output file, delete the uploaded file from the server
        # if a second, third, ... file uploaded, append to the ouput
        # on the go button, GET the correct resource based on timestamp
        return jsonify(error="Upload not yet implemented"), 501

@entryManager.route('/download/<entryid>', methods=['GET'])
def download_entries(entryid):
    return render_template('entrymanager/download.html', stamp=entryid)
