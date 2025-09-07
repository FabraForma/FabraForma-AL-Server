import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash

from database import get_db_connection

# Create the blueprint for the admin UI.
admin_ui_bp = Blueprint('admin_ui', __name__, url_prefix='/admin')

def superadmin_required(view):
    """
    Decorator that redirects to the login page if a super admin is not
    logged in.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user['role'] != 'superadmin':
            return redirect(url_for('admin_ui.login'))
        return view(**kwargs)
    return wrapped_view

@admin_ui_bp.before_app_request
def load_logged_in_user():
    """
    Before each request, check if a user is logged in by looking at the
    session cookie. If so, load their data into the request context `g`.
    """
    user_id = session.get('user_id')
    role = session.get('role')

    if user_id is None or role != 'superadmin':
        g.user = None
    else:
        db = get_db_connection()
        g.user = db.execute(
            'SELECT * FROM users WHERE id = ? AND role = ?', (user_id, 'superadmin')
        ).fetchone()

@admin_ui_bp.route('/login', methods=('GET', 'POST'))
def login():
    """Handles super admin login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db_connection()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND role = ?', (username, 'superadmin')
        ).fetchone()

        if user is None:
            error = 'Incorrect username or user is not a super admin.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'

        if error is None:
            # Store the user's ID and role in the session cookie.
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('admin_ui.dashboard'))

        # If an error occurred, show it on the login page.
        flash(error)

    return render_template('admin_login.html')

@admin_ui_bp.route('/logout', methods=('POST',))
def logout():
    """Logs the user out by clearing the session."""
    session.clear()
    return redirect(url_for('admin_ui.login'))

@admin_ui_bp.route('/companies')
@superadmin_required
def list_companies():
    """Displays a list of all companies in the database."""
    db = get_db_connection()
    companies = db.execute('SELECT id, name FROM companies ORDER BY name').fetchall()
    return render_template('admin_companies.html', companies=companies)

import os
from collections import deque

@admin_ui_bp.route('/logs')
@superadmin_required
def view_logs():
    """Displays the last N lines of the server log file."""
    log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'server.log')
    num_lines = 100
    log_lines = []
    try:
        with open(log_file_path, 'r') as f:
            # Use deque for efficient 'tail' implementation
            log_lines = deque(f, num_lines)
    except FileNotFoundError:
        flash(f"Log file not found at {log_file_path}")
    except Exception as e:
        flash(f"Error reading log file: {e}")

    return render_template('admin_logs.html', log_lines=log_lines, num_lines=num_lines, log_file_path=log_file_path)

@admin_ui_bp.route('/dashboard')
@superadmin_required
def dashboard():
    """Renders the main admin dashboard page."""
    return render_template('admin_dashboard.html')
