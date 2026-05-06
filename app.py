from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, send_file
)
from functools import wraps
import json
import os
import csv
import io
from datetime import datetime

from db import init_db, get_user, create_user, user_exists
from tracker import (
    get_usage_data, get_productivity_score,
    get_ai_suggestions, generate_report_csv
)

# ── App Setup ───────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'detox-secret-key-change-in-production')

# Initialise DB on startup
with app.app_context():
    init_db()


# ── Auth Helpers ────────────────────────────────────────────────
class CurrentUser:
    """Minimal user object stored in session."""
    def __init__(self, data):
        self.id       = data.get('id')
        self.username = data.get('username', 'User')

    @property
    def is_authenticated(self):
        return self.id is not None


def get_current_user():
    user_data = session.get('user')
    if user_data:
        return CurrentUser(user_data)
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user'):
            flash('Please log in to continue.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ── Routes ──────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    current_user = get_current_user()

    # Fetch usage so we can pass serialisable lists to the template.
    # This fixes: TypeError: Object of type Undefined is not JSON serializable
    # if the old index.html uses  {{ times | tojson }}  or  {{ apps | tojson }}
    usage_data = get_usage_data(current_user.id)
    apps  = [a['name']    for a in usage_data.get('apps', [])]
    times = [a['minutes'] for a in usage_data.get('apps', [])]

    return render_template(
        'index.html',
        current_user=current_user,
        apps=apps,       # list[str]   – app names
        times=times,     # list[float] – minutes per app  ← fixes the error
        usage=usage_data,
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('login'))

        user = get_user(username, password)
        if user:
            session['user'] = {'id': user['id'], 'username': user['username']}
            flash(f'Welcome back, {user["username"]}! 👋', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        username         = request.form.get('username', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('register'))

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        if user_exists(username):
            flash('Username already taken. Try another.', 'error')
            return redirect(url_for('register'))

        user = create_user(username, password)
        session['user'] = {'id': user['id'], 'username': user['username']}
        flash('Account created successfully! 🎉', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ── API Endpoints ────────────────────────────────────────────────

@app.route('/api/usage')
@login_required
def api_usage():
    """Return today's app usage data as JSON."""
    user_id = session['user']['id']
    data = get_usage_data(user_id)
    return jsonify(data)


@app.route('/api/score')
@login_required
def api_score():
    """Return productivity score breakdown as JSON."""
    user_id = session['user']['id']
    score = get_productivity_score(user_id)
    return jsonify(score)


@app.route('/api/suggestions')
@login_required
def api_suggestions():
    """Return AI-generated suggestions as JSON."""
    user_id = session['user']['id']
    suggestions = get_ai_suggestions(user_id)
    return jsonify({'suggestions': suggestions})


@app.route('/download_report')
@login_required
def download_report():
    """Stream a CSV report for the current user."""
    user      = get_current_user()
    user_id   = user.id
    csv_data  = generate_report_csv(user_id, user.username)
    filename  = f"detox_report_{datetime.now().strftime('%Y%m%d')}.csv"

    buf = io.BytesIO(csv_data.encode('utf-8'))
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )


# ── Error Handlers ───────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('login.html'), 404  # Redirect to login on 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ── Run ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)