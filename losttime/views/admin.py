#losttime/views/auth.py

from os.path import join
import json
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
import flask_login
from losttime.models import db, User, ClubCode, Event
from losttime.mailman import send_email
from losttime import requires_mod


admin = Blueprint("admin", __name__, static_url_path='/download', static_folder='../static/adminfiles')

@admin.route("/", methods=['GET'])
@flask_login.login_required
def admin_home():
    return redirect(url_for('users.user_home'))

@admin.route("/club_codes", methods=['GET', 'POST'])
@flask_login.login_required
@requires_mod
def admin_club_codes():
    if request.method == 'GET':
        clubs = ClubCode.query.all()
        fname = join(admin.static_folder, 'clubcodes.json')
        with open(fname, 'w+') as f:
            f.write(json.dumps([c.serialize() for c in clubs]))
        return render_template('admin/club_codes.html', 
                               codes=clubs)
    elif request.method == 'POST':
        clubs = ClubCode.query.all()
        existing = {}
        for club in clubs:
            existing["{0}-{1}".format(club.namespace, club.code)] = club
        newclubs = json.load(request.files['clubCodesJSON'])
        matched = 0
        updated = 0
        created = 0
        for newclub in newclubs:
            clubkey = "{0}-{1}".format(newclub['namespace'].upper(), newclub['code'].upper())
            if clubkey in existing.keys():
                up = existing[clubkey]
                if up.name == newclub['name']:
                    matched += 1
                else:
                    up.name = newclub['name']
                    db.session.add(up)
                    updated += 1
            else:
                nc = ClubCode(newclub['namespace'].upper(), newclub['code'].upper(), newclub['name'])
                db.session.add(nc)
                created += 1
        db.session.commit()
        flash("Matched: {} Updated: {} Created: {}".format(matched, updated, created), 'info')
        return "Matched: {} Updated: {} Created: {}".format(matched, updated, created), 201

@admin.route("/users", methods=['GET'])
@flask_login.login_required
@requires_mod
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', 
                           users=users,
                           currentUser = flask_login.current_user)

@admin.route("/events", methods=['GET'])
@flask_login.login_required
@requires_mod
def admin_events():
    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('admin/events.html',
                           events = events)
