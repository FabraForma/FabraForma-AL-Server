import os
import uuid
import click
from flask import Flask
from werkzeug.security import generate_password_hash

def create_app_for_cli():
    """Create a minimal Flask app instance for CLI commands."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dummy-key-for-cli')
    return app

app = create_app_for_cli()

@app.cli.command("createsuperuser")
@click.argument("username")
@click.argument("email")
@click.argument("password")
def create_super_user(username, email, password):
    """
    Creates a new super admin user with the given credentials.
    Example: flask createsuperuser myadmin admin@example.com mypassword
    """
    from database import get_db_connection

    print(f"Creating a new super admin user: {username}")

    if not all([username, email, password]):
        print("Error: Username, email, and password cannot be empty.")
        return

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username or email already exists
        user_exists = cursor.execute(
            "SELECT id FROM users WHERE lower(username) = lower(?) OR lower(email) = lower(?)",
            (username, email)
        ).fetchone()

        if user_exists:
            print(f"Error: A user with that username or email already exists.")
            return

        # Hash the password and create the user
        password_hash = generate_password_hash(password)
        user_id = str(uuid.uuid4())

        # company_id is NULL for super admins
        cursor.execute(
            "INSERT INTO users (id, username, email, password_hash, company_id, role) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, email, password_hash, None, 'superadmin')
        )

        conn.commit()
        print(f"Super admin '{username}' created successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()
