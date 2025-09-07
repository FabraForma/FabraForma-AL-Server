import os
from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from fabraforma_server.server import admin_required, get_safe_path, save_app_config, load_app_config

admin_bp = Blueprint('server_admin', __name__, url_prefix='/server')

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def handle_server_settings():
    if request.method == 'POST':
        try:
            settings_data = request.get_json()
            if not isinstance(settings_data, dict):
                return jsonify({"error": "Invalid format, expected a JSON object"}), 400
            save_app_config(settings_data)
            return jsonify({"status": "success", "message": "Settings saved."})
        except Exception as e:
            raise e
    else:
        return jsonify(load_app_config())

@admin_bp.route('/files/', defaults={'subpath': ''})
@admin_bp.route('/files/<path:subpath>')
@admin_required
def list_files(subpath):
    safe_path = get_safe_path(subpath)
    if not safe_path or not os.path.isdir(safe_path):
        return jsonify({"error": "Invalid or inaccessible path"}), 404
    try:
        file_list = []
        for item in os.listdir(safe_path):
            try:
                item_path = os.path.join(safe_path, item)
                is_dir = os.path.isdir(item_path)
                file_list.append({
                    "name": item,
                    "type": "dir" if is_dir else "file",
                    "size": 0 if is_dir else os.path.getsize(item_path)
                })
            except OSError:
                continue
        return jsonify(file_list)
    except Exception as e:
        raise e

@admin_bp.route('/upload/', defaults={'subpath': ''}, methods=['POST'])
@admin_bp.route('/upload/<path:subpath>', methods=['POST'])
@admin_required
def upload_file(subpath):
    safe_path = get_safe_path(subpath)
    if not safe_path or not os.path.isdir(safe_path):
        return jsonify({"error": "Invalid destination"}), 400
    if 'file' not in request.files or not request.files['file'].filename:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(os.path.join(safe_path, filename))
    return jsonify({"status": "success", "message": f"File '{filename}' uploaded."})

@admin_bp.route('/download/<path:filepath>')
@admin_required
def download_server_file(filepath):
    safe_path = get_safe_path(filepath)
    if not safe_path or not os.path.isfile(safe_path):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(os.path.dirname(safe_path), os.path.basename(safe_path), as_attachment=True)
