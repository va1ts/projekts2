from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import logging

auth = Blueprint('auth', __name__)

# CSV file to store user data
USER_DB_FILE = 'users.csv'

# Load users from CSV into a dictionary for easy lookup
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

# Save user data to CSV
def save_user(username, password_hash, role='user'):
    with open(USER_DB_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'password', 'role'])
        # If the file is empty, write the header
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow({'username': username, 'password': password_hash, 'role': role})

users = load_users()

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash("Username already exists.", "warning")
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
        username = request.form['username']
        password = request.form['password']

        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username
            flash("Login successful.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials.", "danger")

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('auth.login'))