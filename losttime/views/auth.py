#losttime/views/auth.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
import flask_login
from losttime.models import db, User
from losttime import tokenTimedSerializer as tts

auth = Blueprint("auth", __name__, static_url_path='/')

@auth.route("/join", methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('auth/join.html')
    elif request.method == 'POST':
        email = request.form.get("email")
        if User.query.filter_by(email=email).first() != None:
            flash('Hmm, that email address is already registered.', 'warning')
            return redirect(url_for('join'))
        pw1 = request.form.get("pw1")
        if len(pw1) < 6:
            flash ('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('join'))
        pw2 = request.form.get("pw2")
        if pw1 != pw2:
            flash('Those passwords are not the same.', 'danger')
            return redirect(url_for('join'))
        new_user = User(email, pw1)
        db.session.add(new_user)
        db.session.commit()
        sent = send_verification_email(new_user)
        if sent[0]:
            flash("Thanks! Check your email to activate your account.", 'info')
        else:
            flash(sent[1], 'warning')
        return redirect(url_for('index'))

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    elif request.method == 'POST':
        form_email = request.form.get("email")
        the_user = User.query.filter_by(email=form_email).first()
        if the_user is None:
            flash("Hmm, I do not recognize that user", 'warning')
            return redirect(url_for('login'))
        if the_user.is_correct_password(request.form.get("pw")):
            flask_login.login_user(the_user)
            flash("Logged in.", 'success')
            return redirect(url_for('index'))
        flash("Hmm, that password is not correct", 'danger')
        return redirect(url_for('login'))

@auth.route("/logout")
def logout():
    flask_login.logout_user()
    flash("You have logged out.", 'info')
    return redirect(url_for('index'))

@auth.route("/verify-email/<token>", methods=['GET'])
def verify_email(token):
    try:
        email = ts.loads(token, salt='verify-email', max_age=60*60*24)
    except:
        abort(404)
    user = User.query.filter_by(email=email).first_or_404()
    user.isVerified = True
    db.session.add(user)
    db.session.commit()
    flash("Thanks for confirming your email address!", 'info')
    return redirect(url_for('index'))

@auth.route("/verify-email-resend")
@flask_login.login_required
def reconfirm_email():
    u = User.query.get(flask_login.current_user.id)
    if u.isVerified:
        flash("Your email is already confirmed", 'info')
    elif u.email != None:
        sent = send_verification_email(u)
        if sent[0]:
            flash("Email sent. Please click the link within 24 hours to confirm.", 'info')
        else:
            flash(sent[1], 'error')
    else:
        flash("Please enter an email address", 'error')
    return redirect(url_for('index'))

def send_verification_email(user):
    SUBJECT = "Confirm your e-mail for Lost Time Orienteering"
    SEND_FROM = 'Lost Time Orienteering <bot@losttimeorienteering.com>'
    try:
        token = tts.dumps(user.email, salt='verify-email')
        confirm_url = url_for('verify_email', token=token, _external=True)
        HTML = render_template(
            'auth/verify_email_message.html',
            url=confirm_url
        )
    except:
        msg = 'Something went wrong creating the message.'
        return (False, msg)
    try:
        EMAIL = user.email
        # TODO:implement a mailman
        print EMAIL
        print HTML
        #mailman.send_email(SEND_FROM, EMAIL, SUBJECT, HTML)
    except:
        msg = 'Something went wrong sending the message.'
        return (False, msg)
    return (True, EMAIL)
