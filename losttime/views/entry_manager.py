#losttime/views/entry_manager.py

from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from datetime import datetime
from losttime import entryfiles
from _output_templates import EntryWriter
import re
import csv
from os import remove
from os.path import join, isfile

entryManager = Blueprint("entryManager", __name__, static_url_path='/download', static_folder='../static/userfiles')

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
        return render_template('entrymanager/upload.html', stamp=timestamp)

    elif request.method == 'POST':
        infiles = []
        for k in request.files.keys():
            filenum = re.search(r'\[\d+\]', k).group().strip('[]')
            filename = 'entry_{0}_{1}.csv'.format(request.form['stamp'], filenum)
            try:
                infile = entryfiles.save(request.files[k], name=filename)
                infiles.append(entryfiles.path(infile))
            except:
                return jsonify(error="Server error: Failed to save file"), 500

        writer = EntryWriter(infiles, 'OE', request.form['entry-type'])
        try:
            doc = writer.writeEntries()
        except:
            for path in infiles:
                remove(path)
            return jsonify(error="Unable to parse entries from this csv file"), 400
        outfilename = join(entryManager.static_folder, 'EntryForOE-{0}.csv'.format(request.form['stamp']))
        with open(outfilename, 'w') as out:
            out.write(doc)
        for path in infiles:
            remove(path)
        return jsonify(stamp=request.form['stamp']), 201

@entryManager.route('/entries/<entryid>', methods=['GET'])
def download_entries(entryid):
    """Generate page for users to download entries file

    Determines if the requested file exists, renders page or sends 404
    """
    entryfn = 'EntryForOE-{0}.csv'.format(entryid)
    if isfile(join(entryManager.static_folder, entryfn)):
        stats = _entries_stats(join(entryManager.static_folder, entryfn))
        return render_template('entrymanager/download.html', entryfn=entryfn, stats=stats)
    return("Hmm... we didn't find that file"), 404

def _entries_stats(filename):
    with open(filename, 'r') as f:
        numentries = 0
        categories = []

        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        for line in reader:
            numentries += 1
            if line[25] not in categories:
                categories.append(line[25])
        categories.sort()
    return {'count':numentries, 'categories':categories}
