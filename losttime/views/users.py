#losttime/views/auth.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
import flask_login
from losttime.models import db, User
from losttime.mailman import send_email
from losttime import app

users = Blueprint("users", __name__, static_url_path='/')

@users.route("/me", methods=['GET'])
@flask_login.login_required
def user_home():
    if not flask_login.current_user.isVerified:
        flash("Please Verify Your E-Mail Address")
    return render_template('home/user.html', user=flask_login.current_user)
