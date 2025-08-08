from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')

@auth_bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif User.query.filter_by(email=email).first() is not None:
            error = f"User {email} is already registered."

        if error is None:
            new_user = User(email=email, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

import functools
from flask import g

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None
        user = User.query.filter_by(email=email).first()

        if user is None:
            error = 'Incorrect email.'
        elif not check_password_hash(user.password_hash, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('main.index'))

        flash(error)

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
