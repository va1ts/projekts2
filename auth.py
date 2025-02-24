from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import logging
from datetime import timedelta
import re
import requests

auth = Blueprint('auth', __name__)

USER_DB_FILE = 'users.csv'
LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  

def load_users():
    users = {}
    try:
        with open(USER_DB_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users[row['username']] = {
                    'password': row['password'],
                    'role': row['role']
                }
    except FileNotFoundError:
        logging.warning(f"{USER_DB_FILE} not found, starting with an empty user database.")
    return users

def save_user(username, password_hash, role='user'):
    with open(USER_DB_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'password', 'role'])
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow({'username': username, 'password': password_hash, 'role': role})

def is_strong_password(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(pattern, password)

users = load_users()

def verify_recaptcha(token):
    """Verify reCAPTCHA token with Google."""
    secret_key = current_app.config.get("RECAPTCHA_SECRET_KEY")
    if not secret_key:
        logging.error("RECAPTCHA_SECRET_KEY not set in configuration.")
        return False

    data = {
        'secret': secret_key,
        'response': token
    }
    r = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data)
    result = r.json()
    return result.get("success", False)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Verify the captcha response first.
        recaptcha_token = request.form.get("g-recaptcha-response")
        if not recaptcha_token or not verify_recaptcha(recaptcha_token):
            flash("reCAPTCHA verification failed. Please try again.", "danger")
            return redirect(url_for('auth.register'))

        username = request.form['username'].lower()
        password = request.form['password']

        if username in users:
            flash("Username already exists.", "warning")
            return redirect(url_for('auth.register'))
        
        if not is_strong_password(password):
            flash("Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.", "warning")
            return redirect(url_for('auth.register'))
        
        password_hash = generate_password_hash(password, method='sha256')
        save_user(username, password_hash)
        users[username] = {'password': password_hash, 'role': 'user'}

        flash("Registration successful.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Verify the captcha response first.
        recaptcha_token = request.form.get("g-recaptcha-response")
        if not recaptcha_token or not verify_recaptcha(recaptcha_token):
            flash("reCAPTCHA verification failed. Please try again.", "danger")
            return redirect(url_for('auth.login'))

        username = request.form['username'].lower()
        password = request.form['password']
        remember = 'remember' in request.form

        if username in LOGIN_ATTEMPTS and LOGIN_ATTEMPTS[username]['attempts'] >= MAX_LOGIN_ATTEMPTS:
            flash("Account temporarily locked due to too many failed login attempts.", "danger")
            return redirect(url_for('auth.login'))

        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username
            session['role'] = users[username]['role']
            session.permanent = remember 
            flash("Login successful.", "success")
            LOGIN_ATTEMPTS.pop(username, None) 
            return redirect(url_for('dashboard'))
        else:
            LOGIN_ATTEMPTS.setdefault(username, {'attempts': 0})
            LOGIN_ATTEMPTS[username]['attempts'] += 1
            flash("Invalid credentials.", "danger")

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('auth.login'))

@auth.before_app_request
def make_session_permanent():
    session.permanent = True
    auth.permanent_session_lifetime = timedelta(minutes=30)
