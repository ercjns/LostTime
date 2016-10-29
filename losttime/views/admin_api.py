#losttime/views/admin_api.py

from flask import Blueprint, request, jsonify, Response
from losttime.models import db, Event, EventClass, PersonResult, EventTeamClass, TeamResult, ClubCode
from functools import wraps
import json

from losttime import app

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == app.config.get('ADMIN_USER') and password == app.config.get('ADMIN_PW')

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


admin = Blueprint("admin", __name__)

@admin.route('/')
def home():
    return "Not Implemented", 501

@admin.route('/clubcode', methods=['GET', 'POST'])
@requires_auth
def clubcode():
    if request.method == 'GET':
        clubs = ClubCode.query.all()
        return jsonify(clubs), 200

    if request.method == 'POST':
        clubs = ClubCode.query.all()
        existing = {}
        for club in clubs:
            existing["{0}-{1}".format(club.namespace, club.code)] = club

        newclubs = json.load(request.files[request.files.keys()[0]])
        updated = 0
        created = 0
        for newclub in newclubs:
            clubkey = "{0}-{1}".format(newclub['namespace'].upper(), newclub['code'].upper())
            if clubkey in existing.keys():
                up = existing[clubkey]
                up.name = newclub['name']
                db.session.add(up)
                updated += 1
            else:
                nc = ClubCode(newclub['namespace'].upper(), newclub['code'].upper(), newclub['name'])
                db.session.add(nc)
                created += 1
        db.session.commit()

        return "Updated: {0} Created: {1}".format(updated, created), 201



