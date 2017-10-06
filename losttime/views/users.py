#losttime/views/auth.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
import flask_login
from losttime.models import db, User, Event, Series
from losttime.mailman import send_email
from losttime import app

users = Blueprint("users", __name__, static_url_path='/')

@users.route("/me", methods=['GET'])
@flask_login.login_required
def user_home():
    ltuser = flask_login.current_user
    if not ltuser.isVerified:
        flash("Please Verify Your E-Mail Address")
    my_events = Event.query.filter_by(ltuserid=ltuser.id,replacedbyid=None,isProcessed=True).all()
    my_old_events = Event.query.filter_by(ltuserid=ltuser.id,isProcessed=True).filter(Event.replacedbyid != None).all()
    my_series = Series.query.filter_by(ltuserid=ltuser.id,isProcessed=True).filter(Series.replacedbyid == None).all()
    my_old_series = Series.query.filter_by(ltuserid=ltuser.id,isProcessed=True).filter(Series.replacedbyid != None).all()
    return render_template('home/user.html', 
                           user=ltuser,
                           events=my_events,
                           old_events=my_old_events,
                           series=my_series,
                           old_series=my_old_series)
