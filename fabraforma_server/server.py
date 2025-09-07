import os
import re
import json
import time
import shutil
import sys
import traceback
from datetime import datetime, timedelta
from functools import wraps
import uuid
import secrets
import logging
from logging.handlers import RotatingFileHandler
from io import BytesIO
from pydantic import ValidationError
import jwt
from PIL import Image
import easyocr
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from flask import g
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import utils
from reportlab.lib import colors

from .moderator import NSFWDetector

# This file will now serve as a utility belt for the application.
# It holds helper functions and decorators that are shared across blueprints.

# --- Global Variables ---
# These will be initialized by the app factory.
APP_CONFIG = {}
ocr_reader = None
nsfw_detector = None

# --- Decorators (to be imported by blueprints) ---

def validate_with(model: any):
    """Decorator to validate request JSON against a Pydantic model."""
    from flask import request
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                g.validated_data = model.parse_obj(request.get_json())
                return f(*args, **kwargs)
            except ValidationError as e:
                raise e
            except Exception as e:
                 from flask import current_app
                 current_app.logger.error(f"Error during request parsing before validation: {e}")
                 return jsonify({"error": "Invalid request format. Expected JSON."}), 400
        return decorated_function
    return decorator

def token_required(f):
    from flask import request, jsonify, current_app
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            g.current_user = {
                'user_id': data['user_id'], 'username': data['username'],
                'company_id': data['company_id'], 'role': data['role']
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except Exception as e:
            current_app.logger.warning(f"Invalid token received: {e}")
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from flask import jsonify
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user['role'] != 'admin':
            return jsonify({'message': 'Admin privileges required!'}), 403
        return f(*args, **kwargs)
    return decorated

# --- Helper Functions (to be imported by blueprints) ---

def get_ocr_reader():
    from flask import current_app
    global ocr_reader
    if ocr_reader is None:
        current_app.logger.info("⏳ Loading EasyOCR model into memory...")
        try:
            ocr_reader = easyocr.Reader(['en'], gpu=True)
            current_app.logger.info("✅ EasyOCR model loaded.")
        except Exception as e:
            current_app.logger.critical(f"🛑 FATAL: Could not load EasyOCR model. Error: {e}")
            ocr_reader = None
    return ocr_reader

def get_nsfw_detector():
    global nsfw_detector
    if nsfw_detector is None:
        nsfw_detector = NSFWDetector()
    return nsfw_detector

def get_company_data_path(company_id, *args):
    from flask import current_app
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(script_dir, "..", "data", str(company_id))
    os.makedirs(base_path, exist_ok=True)
    return os.path.join(base_path, *args)

def load_app_config():
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "server_config.json")
        with open(config_path, 'r') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return {}

def save_app_config(data):
    global APP_CONFIG
    config_path = os.path.join(os.path.dirname(__file__), "..", "server_config.json")
    with open(config_path, 'w') as f: json.dump(data, f, indent=4)
    APP_CONFIG = data.copy()

def get_safe_path(subpath):
    share_dir = os.path.abspath(APP_CONFIG.get("SERVER_SHARE_DIR", "server_share"))
    target_path = os.path.abspath(os.path.join(share_dir, subpath))
    if not target_path.startswith(share_dir): return None
    return target_path

def parse_time_string(time_str):
    h_match = re.search(r'(\d+)\s*h', time_str, re.IGNORECASE); h = int(h_match.group(1)) if h_match else 0
    m_match = re.search(r'(\d+)\s*m', time_str, re.IGNORECASE); m = int(m_match.group(1)) if m_match else 0
    s_match = re.search(r'(\d+)\s*s', time_str, re.IGNORECASE); s = int(s_match.group(1)) if s_match else 0
    return round(h + (m / 60.0) + (s / 3600.0), 2)

def calculate_printer_hourly_rate(printer_data):
    try:
        total_cost = printer_data['setup_cost'] + (printer_data['maintenance_cost'] * printer_data['lifetime_years'])
        total_hours = printer_data['lifetime_years'] * 365 * 24 * (printer_data.get('uptime_percent', 50) / 100)
        if total_hours == 0: return 0.0
        return (total_cost / total_hours) + ((printer_data['power_w'] / 1000) * printer_data['price_kwh'])
    except (KeyError, TypeError, ZeroDivisionError): return 0.0

def calculate_cogs_values(form_data, printer_data, filament_data):
    try:
        filament_g = float(form_data.get("Filament (g)", 0)); time_str = form_data.get("Time (e.g. 7h 30m)", "0h 0m")
        labour_time_min = float(form_data.get("Labour Time (min)", 0)); labour_rate_user = float(form_data.get("Labour Rate (₹/hr)", 0))
        print_time_hours = parse_time_string(time_str)
        mat_cost = (filament_data.get('price', 0) / 1000) * filament_g * filament_data.get('efficiency_factor', 1.0)
        labour_cogs = (labour_rate_user / 60) * labour_time_min
        printer_cogs = calculate_printer_hourly_rate(printer_data) * printer_data.get('buffer_factor', 1.0) * print_time_hours
        total_cogs_user = mat_cost + labour_cogs + printer_cogs
        mat_cost_default = (filament_data.get('price', 0) / 1000) * filament_g
        labour_cogs_default = (100 / 60) * labour_time_min
        printer_cogs_default = calculate_printer_hourly_rate(printer_data) * print_time_hours
        total_cogs_default = mat_cost_default + labour_cogs_default + printer_cogs_default
        return {"user_cogs": total_cogs_user, "default_cogs": total_cogs_default}
    except (ValueError, TypeError, KeyError, ZeroDivisionError): return {"user_cogs": 0.0, "default_cogs": 0.0}

def extract_data_from_ocr(company_id, ocr_results):
    from .database import db_session
    from .models import Filament, Printer
    full_text = " ".join([item[1] for item in ocr_results]).lower()
    extracted_data = { "filament": 0.0, "time_str": "0h 0m", "material": None, "detected_printer_id": None }
    # ... (rest of the logic remains the same)
    filaments_q = db_session.query(Filament.material).filter_by(company_id=company_id).distinct()
    known_materials = [m[0].lower() for m in filaments_q]
    for material in known_materials:
        if re.search(r'\b' + re.escape(material) + r'\b', full_text):
            extracted_data["material"] = material.upper()
            break
    printers = db_session.query(Printer).filter_by(company_id=company_id).all()
    for printer in printers:
        if printer.brand.lower() in full_text or printer.model.lower() in full_text:
            extracted_data["detected_printer_id"] = printer.id
            break
    return extracted_data

def update_filament_stock(company_id, final_data):
    from .database import db_session
    from .models import Filament
    try:
        material, brand = final_data.get("Material"), final_data.get("Brand")
        grams_used = float(final_data.get("Filament (g)", 0))
        if not all([material, brand, grams_used > 0]): return
        filament_to_update = db_session.query(Filament).filter_by(company_id=company_id, material=material, brand=brand).first()
        if filament_to_update:
            filament_to_update.stock_g -= grams_used
            db_session.commit()
        else:
            from flask import current_app
            current_app.logger.warning(f"Could not find filament {material}/{brand} for company {company_id} to update stock.")
    except Exception as e:
        db_session.rollback()
        from flask import current_app
        current_app.logger.error(f"Error updating stock for company {company_id}: {e}")

def create_excel_file(company_id, final_data, printer, filament):
    # ... (logic remains the same)
    pass

def log_to_master_excel(company_id, file_path, final_data, user_cogs, default_cogs):
    # ... (logic remains the same)
    pass

def save_app_log(company_id, final_data, cogs_data, local_image_filename):
    # ... (logic remains the same)
    pass

def generate_quotation_pdf(buffer, data):
    # ... (logic remains the same)
    pass

def initialize_app_components():
    """Initializes global components like OCR reader and loads config."""
    global APP_CONFIG
    APP_CONFIG = load_app_config()
    defaults = { "SERVER_SHARE_DIR": "server_share", "TEMPLATE_PATH": "FDM.xlsx", "cells": ["D4", "D9", "D10", "D11", "D12", "D13"],
                 "headers": ["Sr. No", "Date", "Part Number", "Filename", "Material", "Filament Cost (₹/kg)", "Filament (g)", "Time (h)", "Labour Time (min)", "User COGS (₹)", "Default COGS (₹)", "Source Link"] }
    if any(key not in APP_CONFIG for key in defaults.keys()):
        APP_CONFIG = {**defaults, **APP_CONFIG}
        save_app_config(APP_CONFIG)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(script_dir, "..", "data"), exist_ok=True)
    os.makedirs(APP_CONFIG["SERVER_SHARE_DIR"], exist_ok=True)

    get_ocr_reader()
    get_nsfw_detector()
    return True
