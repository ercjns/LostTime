#losttime/views/entry_manager.py

from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from datetime import datetime
from losttime import entryfiles
from ._output_templates import EntryWriter
import re
import csv
from os import remove
from os.path import join, isfile
from collections import Counter

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

        writer = EntryWriter(infiles, request.form['entry-format'], request.form['entry-type'], request.form['entry-punch'])
        try:
            doc = writer.writeEntries()
        except:
            for path in infiles:
                remove(path)
            return jsonify(error="Unable to parse entries from this csv file"), 400
        if request.form['entry-format'] == 'OE':
            outfilename = join(entryManager.static_folder, 'EntryForOE-{0}.csv'.format(request.form['stamp']))
            with open(outfilename, 'w') as out:
                out.write(doc)
        elif request.form['entry-format'] in ['CheckIn', 'CheckInNationalMeet']:
            outfilename = join(entryManager.static_folder, 'EntryForCheckIn-{0}.pdf'.format(request.form['stamp']))
            from weasyprint import HTML
            HTML(string=doc).write_pdf(outfilename, stylesheets=[join(entryManager.static_folder,'CheckInEntries.css')])
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
        stats = _entries_stats_OE(join(entryManager.static_folder, entryfn))
        return render_template('entrymanager/download.html', entryfn=entryfn, stats=stats)

    entryfn = 'EntryForCheckIn-{0}.pdf'.format(entryid)
    if isfile(join(entryManager.static_folder, entryfn)):
        return render_template('entrymanager/download.html', entryfn=entryfn)

    return("Hmm... we didn't find that file"), 404

def _entries_stats_OE(filename):
    with open(filename, 'r') as f:
        numentries = 0
        categories = []

        reader = csv.reader(f, delimiter=';')
        next(reader) #skip the header line
        for line in reader:
            numentries += 1
            categories.append(line[25])

        cats = sorted(Counter(categories).items(), key=lambda x: x[0])

        if cats[0][0] == '':
            cats[0] = ('NO CLASS', cats[0][1])
    return {'count':numentries, 'categories':cats}
