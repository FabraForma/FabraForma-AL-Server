import os
import time
from flask import Blueprint, jsonify, request, g, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from fabraforma_server.database import db_session
from fabraforma_server.models import User
from fabraforma_server.validators import ChangePasswordModel, UpdateProfileModel
from fabraforma_server.server import validate_with, token_required, get_company_data_path

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_user_profile():
    user_id = g.current_user['user_id']
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    profile_data = {
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
        "dob": user.dob,
        "profile_picture_path": user.profile_picture_path
    }
    if profile_data.get('profile_picture_path'):
        profile_data['profile_picture_url'] = f"{request.url_root.rstrip('/')}/user/profile_picture/{profile_data['profile_picture_path']}"
    return jsonify(profile_data)

@user_bp.route('/profile', methods=['POST'])
@token_required
@validate_with(UpdateProfileModel)
def update_user_profile():
    data = g.validated_data
    user_id = g.current_user['user_id']

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    update_data = data.dict(exclude_unset=True)
    if not update_data:
        return jsonify({'message': 'No update information provided'}), 400

    try:
        for key, value in update_data.items():
            setattr(user, key, value)
        db_session.commit()
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        db_session.rollback()
        raise e

@user_bp.route('/change_password', methods=['POST'])
@token_required
@validate_with(ChangePasswordModel)
def change_password():
    data = g.validated_data
    user_id = g.current_user['user_id']

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user or not check_password_hash(user.password_hash, data.current_password):
        return jsonify({'message': 'Current password is not correct'}), 403

    try:
        user.password_hash = generate_password_hash(data.new_password)
        db_session.commit()
        return jsonify({'message': 'Password updated successfully'})
    except Exception as e:
        db_session.rollback()
        raise e

@user_bp.route('/profile_picture', methods=['POST'])
@token_required
def upload_profile_picture():
    user_id = g.current_user['user_id']
    company_id = g.current_user['company_id']

    if 'file' not in request.files or not request.files['file'].filename:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    # The NSFW check will be handled by a decorator or middleware in the final version
    # For now, we assume it's done before the request hits the blueprint
    # from fabraforma_server.server import nsfw_detector
    # is_safe, reason = nsfw_detector.is_image_safe(file.read()) ...

    filename = secure_filename(f"{user_id}_{int(time.time())}{os.path.splitext(file.filename)[1]}")
    upload_folder = get_company_data_path(company_id, "profile_pictures")
    file.save(os.path.join(upload_folder, filename))

    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        user.profile_picture_path = filename
        db_session.commit()
        new_url = f"{request.url_root.rstrip('/')}/user/profile_picture/{filename}"
        return jsonify({'message': 'Profile picture updated', 'filepath': filename, 'url': new_url})
    except Exception as e:
        db_session.rollback()
        raise e

@user_bp.route('/profile_picture/<path:filename>')
@token_required
def serve_profile_picture(filename):
    company_id = g.current_user['company_id']
    directory = get_company_data_path(company_id, "profile_pictures")
    return send_from_directory(directory, filename)
