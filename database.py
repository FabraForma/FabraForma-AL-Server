# database.py
import sqlite3
import json
import os
import uuid
import time
from werkzeug.security import generate_password_hash

DB_FILE = "server_data.sqlite"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(script_dir):
    if os.path.exists(DB_FILE):
        # --- MODIFIED: Check if the table needs updating ---
        conn_check = get_db_connection()
        cursor_check = conn_check.cursor()
        try:
            # Check for the existence of the new 'email' column
            cursor_check.execute("SELECT email FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("INFO: Older database schema detected. Adding new profile columns to 'users' table...")
            cursor_check.execute("ALTER TABLE users ADD COLUMN email TEXT")
            cursor_check.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
            cursor_check.execute("ALTER TABLE users ADD COLUMN dob TEXT")
            cursor_check.execute("ALTER TABLE users ADD COLUMN profile_picture_path TEXT")
            # Make the email column unique after adding it
            cursor_check.execute("CREATE UNIQUE INDEX idx_users_email ON users (email)")
            print("✅ Database schema updated.")
        conn_check.close()
        return

    print("INFO: Database not found. Initializing new database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('CREATE TABLE companies (id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
    
    # --- MODIFIED: Added email and profile fields to the users table ---
    cursor.execute('''
    CREATE TABLE users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        company_id TEXT NOT NULL,
        role TEXT NOT NULL,
        phone_number TEXT,
        dob TEXT,
        profile_picture_path TEXT,
        FOREIGN KEY (company_id) REFERENCES companies (id),
        UNIQUE (username, company_id)
    )''')

    cursor.execute('''
    CREATE TABLE printers (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL, brand TEXT, model TEXT, setup_cost REAL,
        maintenance_cost REAL, lifetime_years INTEGER, power_w REAL, price_kwh REAL,
        buffer_factor REAL, uptime_percent REAL, FOREIGN KEY (company_id) REFERENCES companies (id)
    )''')
    cursor.execute('''
    CREATE TABLE filaments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, company_id TEXT NOT NULL, material TEXT NOT NULL,
        brand TEXT NOT NULL, price REAL, stock_g REAL, efficiency_factor REAL,
        FOREIGN KEY (company_id) REFERENCES companies (id), UNIQUE (company_id, material, brand)
    )''')
    conn.commit()
    print("✅ Database tables created successfully.")

    # Create default company and data since no migration path exists for new columns
    print("INFO: Creating default company and data.")
    default_company_id = "fabraforma_default"
    default_password_hash = generate_password_hash("password")

    cursor.execute("INSERT INTO companies (id, name) VALUES (?, ?)", (default_company_id, "FabraForma"))
    
    # --- MODIFIED: Added email for the default user ---
    default_email = f"admin@{default_company_id}.com"
    cursor.execute("INSERT INTO users (id, username, email, password_hash, company_id, role) VALUES (?, ?, ?, ?, ?, ?)",
                   (str(uuid.uuid4()), "admin", default_email, default_password_hash, default_company_id, "admin"))
    print(f"  -> Created default admin user (login with email: {default_email} and password: password).")

    cursor.execute("""
        INSERT INTO printers (id, company_id, brand, model, setup_cost, maintenance_cost, lifetime_years, power_w, price_kwh, buffer_factor, uptime_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(time.time()), default_company_id, "Bambu Lab", "P1S", 70000, 5000, 5, 300, 8.0, 1.0, 50))
    print("  -> Created default printer.")

    default_filaments = [
        (default_company_id, "PLA", "Generic", 1200, 1000, 1.0),
        (default_company_id, "PETG", "Generic", 1400, 1000, 1.0)
    ]
    cursor.executemany("""
        INSERT INTO filaments (company_id, material, brand, price, stock_g, efficiency_factor)
        VALUES (?, ?, ?, ?, ?, ?)""", default_filaments)
    print("  -> Created default filaments.")

    conn.commit()
    conn.close()
    print("✅ Database initialization complete.")