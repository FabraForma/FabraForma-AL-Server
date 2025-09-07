import os
import re
import json
import time
from io import BytesIO
from flask import Blueprint, jsonify, request, g, send_from_directory, current_app
from pydantic import ValidationError
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import utils
from reportlab.lib import colors
from werkzeug.utils import secure_filename

from fabraforma_server.database import db_session
from fabraforma_server.models import Printer, Filament
from fabraforma_server.validators import ProcessImageModel, GenerateQuotationModel
from fabraforma_server.server import (
    token_required, get_company_data_path, get_ocr_reader, get_nsfw_detector,
    parse_time_string, calculate_cogs_values, extract_data_from_ocr,
    update_filament_stock, create_excel_file, log_to_master_excel,
    save_app_log, generate_quotation_pdf
)

processing_bp = Blueprint('processing', __name__)

@processing_bp.route('/images/<path:filename>')
@token_required
def serve_image(filename):
    image_dir = get_company_data_path(g.current_user['company_id'], "local_log_images")
    return send_from_directory(image_dir, filename)

@processing_bp.route('/ocr_upload', methods=['POST'])
@token_required
def ocr_upload():
    if 'image' not in request.files: return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    image_bytes = file.read()
    file.seek(0)

    nsfw_detector = get_nsfw_detector()
    is_safe, reason = nsfw_detector.is_image_safe(image_bytes)
    if not is_safe:
        return jsonify({'error': 'Image upload rejected', 'message': reason}), 400

    reader = get_ocr_reader()
    if not reader: return jsonify({"error": "OCR model not available."}), 503

    ocr_results = reader.readtext(image_bytes)
    return jsonify(extract_data_from_ocr(g.current_user['company_id'], ocr_results))

from .tasks import process_verified_image
import base64

@processing_bp.route('/process_image', methods=['POST'])
@token_required
def process_image_upload():
    company_id = g.current_user['company_id']
    if 'image' not in request.files or 'json' not in request.form:
        return jsonify({"error": "Missing image or data"}), 400

    try:
        final_data_model = ProcessImageModel.parse_raw(request.form['json'])
        final_data = final_data_model.dict(by_alias=True)
    except (ValidationError, KeyError, json.JSONDecodeError) as e:
        return jsonify({"error": "Invalid or missing 'json' field in form data", "details": str(e)}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()

    nsfw_detector = get_nsfw_detector()
    is_safe, reason = nsfw_detector.is_image_safe(image_bytes)
    if not is_safe:
        return jsonify({'error': 'Image upload rejected', 'message': reason}), 400

    # Encode image bytes to safely pass to Celery task
    image_bytes_b64 = base64.b64encode(image_bytes).decode('utf-8')

    # Dispatch the long-running task to Celery
    task = process_verified_image.delay(
        company_id=company_id,
        final_data=final_data,
        image_filename=image_file.filename,
        image_bytes_b64=image_bytes_b64
    )

    # Immediately return a response to the client
    return jsonify({
        "status": "processing",
        "message": "Image processing has been queued.",
        "task_id": task.id
    }), 202

@processing_bp.route('/generate_quotation', methods=['POST'])
@token_required
def generate_quotation():
    company_id = g.current_user['company_id']
    try:
        data = GenerateQuotationModel.parse_raw(request.form['json'])
    except (ValidationError, KeyError, json.JSONDecodeError) as e:
        return jsonify({"error": "Invalid or missing 'json' field in form data", "details": str(e)}), 400

    logo_path = None
    if 'logo' in request.files and request.files['logo'].filename:
        logo_file = request.files['logo']
        image_bytes = logo_file.read()
        logo_file.seek(0)

        nsfw_detector = get_nsfw_detector()
        is_safe, reason = nsfw_detector.is_image_safe(image_bytes)
        if not is_safe:
            return jsonify({'error': 'Logo upload rejected', 'message': reason}), 400

        uploads_folder = get_company_data_path(company_id, "uploads")
        logo_path = os.path.join(uploads_folder, secure_filename(logo_file.filename))
        logo_file.save(logo_path)
        data.company_details.logo_path = logo_path

    buffer = BytesIO()
    generate_quotation_pdf(buffer, data.dict())
    buffer.seek(0)

    customer_name_safe = re.sub(r'[^a-zA-Z0-9_]', '', data.customer_name.replace(' ', '_'))
    filename = f"Quotation_{customer_name_safe}_{int(time.time())}.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@processing_bp.route('/download/log/<path:filename>')
@token_required
def download_log_file(filename):
    excel_dir = get_company_data_path(g.current_user['company_id'], "Excel_Logs")
    return send_from_directory(os.path.abspath(excel_dir), filename, as_attachment=True)

@processing_bp.route('/download/masterlog/<year_month>')
@token_required
def download_master_log_file(year_month):
    filename = f"master_log_{year_month.split('_')[1]}.xlsx"
    directory = get_company_data_path(g.current_user['company_id'], "Monthly_Expenditure", year_month)
    return send_from_directory(os.path.abspath(directory), filename, as_attachment=True)

@processing_bp.route('/logs', methods=['GET'])
@token_required
def get_logs():
    log_path = get_company_data_path(g.current_user['company_id'], "app_logs.json")
    try:
        with open(log_path, 'r') as f: return jsonify(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError): return jsonify([])

@processing_bp.route('/processed_log', methods=['GET'])
@token_required
def get_processed_log():
    log_path = get_company_data_path(g.current_user['company_id'], "processed_log.json")
    try:
        with open(log_path, 'r') as f: return jsonify(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError): return jsonify([])
