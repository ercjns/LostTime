#losttime/views/auth.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
import flask_login
from losttime.models import db, User
from losttime import tokenTimedSerializer as tts
from losttime.mailman import send_email
from losttime import app

auth = Blueprint("auth", __name__, static_url_path='/')

@auth.route("/join", methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('auth/join.html')
    elif request.method == 'POST':
        email = request.form.get("email").lower()
        if User.query.filter_by(email=email).first() != None:
            flash('Hmm, that email address is already registered.', 'warning')
            return redirect(url_for('auth.join'))
        pw1 = request.form.get("pw1")
        if len(pw1) < 6:
            flash ('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.join'))
        pw2 = request.form.get("pw2")
        if pw1 != pw2:
            flash('Those passwords are not the same.', 'danger')
            return redirect(url_for('auth.join'))
        new_user = User(email, pw1)
        db.session.add(new_user)
        db.session.commit()
        sent = send_verification_email(new_user)
        if sent[0]:
            flash("Thanks! Check your email to activate your account.", 'info')
            if app.config['FLASH_EMAILS']:
                flash(sent[1], 'info')
        else:
            flash(sent[1], 'warning')
        return redirect(url_for('home_page'))

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    elif request.method == 'POST':
        form_email = request.form.get("email").lower()
        the_user = User.query.filter_by(email=form_email).first()
        if the_user is None:
            flash("Hmm, I do not recognize that user", 'warning')
            return redirect(url_for('auth.login'))
        if the_user.is_correct_password(request.form.get("pw")):
            flask_login.login_user(the_user)
            flash("Logged in.", 'success')
            return redirect(url_for('home_page'))
        flash("Hmm, that password is not correct", 'danger')
        return redirect(url_for('login'))

@auth.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    flash("You have logged out.", 'info')
    return redirect(url_for('home_page'))

@auth.route("/verify-email/<token>", methods=['GET'])
def verify_email(token):
    try:
        email = tts.loads(token, salt='verify-email', max_age=60*60*24)
    except:
        abort(404)
    user = User.query.filter_by(email=email).first_or_404()
    user.isVerified = True
    db.session.add(user)
    db.session.commit()
    flash("Thanks for confirming your email address!", 'info')
    return redirect(url_for('home_page'))

@auth.route("/request-password-reset", methods=['GET', 'POST'])
def request_password_reset():
    if request.method == 'GET':
        return render_template('auth/request_reset.html')
    elif request.method == 'POST':
        form_email = request.form.get("email").lower()
        try:
            the_user = User.query.filter_by(email=form_email).first()
            if the_user.isVerified:
                sent = send_password_reset(the_user)
                if sent[0] and app.config['FLASH_EMAILS']:
                    flash(sent[1], 'info')
        except:
            app.logger.warning('PW reset requested for unknown email {}'.format(form_email))
        flash("Check your email for a link to reset your password.")
        return redirect(url_for('home_page'))

@auth.route("/reset-password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'GET':
        try:
            email = tts.loads(token, salt='reset-pw', max_age=60*15)
        except:
            abort(404)
        user = User.query.filter_by(email=email).first_or_404()
        return render_template('auth/reset.html', user=user, token=token)
    elif request.method == 'POST':
        try:
            email = tts.loads(token, salt='reset-pw', max_age=60*15)
        except:
            flash("Sorry, this page has expired.")
            return redirect(url_for('home_page'))
        user = User.query.filter_by(email=email).first_or_404()
        user.password = request.form.get("pw1")
        db.session.add(user)
        db.session.commit()
        flash("Password updated", 'info')
        return redirect(url_for('home_page'))

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
            if app.config['FLASH_EMAILS']:
                flash(sent[1], 'info')
        else:
            flash(sent[1], 'error')
    else:
        flash("Please enter an email address", 'error')
    return redirect(url_for('users.user_home'))

def send_verification_email(user):
    SUBJECT = "Confirm your e-mail for Lost Time Orienteering"
    SEND_FROM = 'Lost Time Orienteering <bot@losttimeorienteering.com>'
    try:
        token = tts.dumps(user.email, salt='verify-email')
        confirm_url = url_for('auth.verify_email', token=token, _external=True)
        HTML = render_template(
            'auth/verify_email_message.html',
            url=confirm_url
        )
    except:
        app.logger.error('Failed to create verification email for {}'.format(user.email))
        msg = 'Something went wrong.'
        return (False, msg)
    try:
        EMAIL = user.email
        msg = send_email(SEND_FROM, EMAIL, SUBJECT, HTML)
        app.logger.info('Sent verification email to {}'.format(EMAIL))
    except:
        app.logger.error('Failed to send verification email for {}'.format(EMAIL))
        msg = 'Something went wrong.'
        return (False, msg)
    return (True, msg)

def send_password_reset(user):
    SUBJECT = "Confirm your e-mail for Lost Time Orienteering"
    SEND_FROM = 'Lost Time Orienteering <bot@losttimeorienteering.com>'
    try:
        token = tts.dumps(user.email, salt='reset-pw')
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        HTML = render_template(
            'auth/reset_pw_message.html',
            url=rest_url
        )
    except:
        msg = 'Something went wrong creating the message.'
        return (False, msg)
    try:
        EMAIL = user.email
        msg = send_email(SEND_FROM, EMAIL, SUBJECT, HTML)
        app.logger.info('Sent PW reset email to {}'.format(EMAIL))
    except:
        msg = 'Something went wrong sending the message.'
        return (False, msg)
    return (True, msg)
