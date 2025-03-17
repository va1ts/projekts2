from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import logging
from datetime import timedelta
import re

auth = Blueprint('auth', __name__)

DB_FILE = 'airaware.db'
LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  # Lockout time in seconds

def get_db():
    """Establish a connection to the database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_users():
    """Load all users from the database."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = {
            row['username']: {
                'password': row['password'],
                'role': row['role']
            } for row in cursor.fetchall()
        }
        conn.close()
        return users
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return {}

def save_user(username, password_hash, role='user'):
    """Save a new user to the database."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
            (username, password_hash, role)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error saving user: {e}")
        raise

def is_strong_password(password):
    """Check if a password meets the strength requirements."""
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(pattern, password)

# Load users into memory
users = load_users()

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
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
    """Handle user login."""
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        remember = 'remember' in request.form

        # Check for lockout due to too many failed attempts
        if username in LOGIN_ATTEMPTS and LOGIN_ATTEMPTS[username]['attempts'] >= MAX_LOGIN_ATTEMPTS:
            flash("Account temporarily locked due to too many failed login attempts.", "danger")
            return redirect(url_for('auth.login'))

        # Validate credentials
        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username
            session.permanent = remember
            flash("Login successful.", "success")
            LOGIN_ATTEMPTS.pop(username, None)  # Reset login attempts
            return redirect(url_for('dashboard'))
        else:
            LOGIN_ATTEMPTS.setdefault(username, {'attempts': 0})
            LOGIN_ATTEMPTS[username]['attempts'] += 1
            flash("Invalid credentials.", "danger")

    return render_template('login.html')

@auth.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('auth.login'))

@auth.before_app_request
def make_session_permanent():
    """Ensure session is permanent and set session lifetime."""
    session.permanent = True
    auth.permanent_session_lifetime = timedelta(minutes=30)