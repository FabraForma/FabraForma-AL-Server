import uuid
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, g
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from fabraforma_server.database import db_session
from fabraforma_server.models import User, Company, AuthToken
from fabraforma_server.validators import (
    LoginModel, RegisterCompanyModel, CreateUserModel
)
from fabraforma_server.server import validate_with, token_required, admin_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/companies', methods=['GET'])
def get_companies():
    companies = db_session.query(Company).order_by(Company.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in companies])

@auth_bp.route('/login', methods=['POST'])
@validate_with(LoginModel)
def login():
    data = g.validated_data
    from sqlalchemy import or_

    user = db_session.query(User).filter(
        or_(User.email.ilike(data.identifier), User.username.ilike(data.identifier))
    ).first()

    if not user or not check_password_hash(user.password_hash, data.password):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = jwt.encode({
        'user_id': user.id, 'username': user.username, 'company_id': user.company_id,
        'role': user.role, 'exp': datetime.utcnow() + timedelta(hours=24)
    }, g.current_app.config['SECRET_KEY'], algorithm="HS256")

    response_data = {'token': access_token}

    if data.remember_me:
        remember_token = secrets.token_hex(32)
        token_hash = generate_password_hash(remember_token)
        expires_at = datetime.utcnow() + timedelta(days=30)
        try:
            new_token = AuthToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at.isoformat()
            )
            db_session.add(new_token)
            db_session.commit()
            response_data['remember_token'] = remember_token
        except Exception as e:
            db_session.rollback()
            g.current_app.logger.error(f"Could not save remember token: {e}")

    return jsonify(response_data)

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.json
    remember_token = data.get('remember_token')
    if not remember_token:
        return jsonify({'message': 'Remember token is missing'}), 401

    all_tokens = db_session.query(AuthToken).all()
    user_id = None
    token_to_delete = None

    for token_obj in all_tokens:
        if check_password_hash(token_obj.token_hash, remember_token):
            if datetime.utcnow() < datetime.fromisoformat(token_obj.expires_at):
                user_id = token_obj.user_id
                break
            else:
                token_to_delete = token_obj
                break

    if token_to_delete:
        db_session.delete(token_to_delete)
        db_session.commit()
        return jsonify({'message': 'Remember token has expired'}), 401

    if not user_id:
        return jsonify({'message': 'Invalid or expired remember token'}), 401

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'message': 'User associated with token not found'}), 404

    access_token = jwt.encode({
        'user_id': user.id, 'username': user.username, 'company_id': user.company_id,
        'role': user.role, 'exp': datetime.utcnow() + timedelta(hours=24)
    }, g.current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': access_token})

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    data = request.json
    remember_token = data.get('remember_token')
    if remember_token:
        user_tokens = db_session.query(AuthToken).filter_by(user_id=g.current_user['user_id']).all()
        for token_obj in user_tokens:
            if check_password_hash(token_obj.token_hash, remember_token):
                db_session.delete(token_obj)
                db_session.commit()
                break
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/register_company', methods=['POST'])
@validate_with(RegisterCompanyModel)
def register_company():
    data = g.validated_data
    if db_session.query(Company).filter(Company.name.ilike(data.company_name)).first():
        return jsonify({'message': 'A company with this name already exists'}), 409
    if db_session.query(User).filter(User.email.ilike(data.admin_email)).first():
        return jsonify({'message': 'This email is already registered'}), 409

    try:
        new_company = Company(id=str(uuid.uuid4()), name=data.company_name)
        new_admin = User(
            id=str(uuid.uuid4()),
            username=data.admin_username,
            email=data.admin_email,
            password_hash=generate_password_hash(data.admin_password),
            role='admin',
            company=new_company
        )
        db_session.add(new_company)
        db_session.add(new_admin)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e

    return jsonify({'message': f"Company '{data.company_name}' created successfully."}), 201

@auth_bp.route('/create_user', methods=['POST'])
@admin_required
@validate_with(CreateUserModel)
def create_user():
    data = g.validated_data
    company_id = g.current_user['company_id']
    if db_session.query(User).filter(User.email.ilike(data.email)).first():
        return jsonify({'message': 'This email is already registered'}), 409
    if db_session.query(User).filter(User.username.ilike(data.username), User.company_id == company_id).first():
        return jsonify({'message': 'This username already exists in your company'}), 409

    try:
        new_user = User(
            id=str(uuid.uuid4()),
            username=data.username,
            email=data.email,
            password_hash=generate_password_hash(data.password),
            company_id=company_id,
            role=data.role
        )
        db_session.add(new_user)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e

    return jsonify({'message': f"User '{data.username}' created successfully."}), 201
