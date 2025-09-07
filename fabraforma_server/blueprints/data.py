from flask import Blueprint, jsonify, request, g
from pydantic import ValidationError

from fabraforma_server.database import db_session
from fabraforma_server.models import Printer, Filament
from fabraforma_server.validators import PrinterModel, FilamentsPostModel
from fabraforma_server.server import token_required

data_bp = Blueprint('data', __name__)

@data_bp.route('/printers', methods=['GET', 'POST'])
@token_required
def handle_printers():
    company_id = g.current_user['company_id']
    if request.method == 'POST':
        printers_data = request.get_json()
        if not isinstance(printers_data, list):
            return jsonify({"error": "Request body must be a list of printers"}), 400

        try:
            validated_printers = [PrinterModel.parse_obj(p).dict() for p in printers_data]
        except ValidationError as e:
            raise e

        try:
            db_session.query(Printer).filter_by(company_id=company_id).delete()
            new_printers = [Printer(**{**p, 'company_id': company_id}) for p in validated_printers]
            if new_printers:
                db_session.add_all(new_printers)
            db_session.commit()
            return jsonify({"status": "saved"})
        except Exception as e:
            db_session.rollback()
            raise e
    else: # GET
        printers = db_session.query(Printer).filter_by(company_id=company_id).all()
        printers_list = [
            {c.name: getattr(p, c.name) for c in p.__table__.columns} for p in printers
        ]
        return jsonify(printers_list)

@data_bp.route('/filaments', methods=['GET', 'POST'])
@token_required
def handle_filaments():
    company_id = g.current_user['company_id']
    if request.method == 'POST':
        filaments_data = request.get_json()
        if not isinstance(filaments_data, dict):
            return jsonify({"error": "Request body must be a dictionary of materials"}), 400

        validated_filaments = {}
        try:
            for material, brands in filaments_data.items():
                if not isinstance(brands, dict):
                     raise ValidationError([{"loc": [material], "msg": "Brand data must be a dictionary"}], model=FilamentsPostModel)
                validated_brands = {}
                for brand, details in brands.items():
                    validated_brands[brand] = FilamentsPostModel.parse_obj(details).dict()
                validated_filaments[material] = validated_brands
        except ValidationError as e:
            raise e

        try:
            db_session.query(Filament).filter_by(company_id=company_id).delete()
            new_filaments = []
            for material, brands in validated_filaments.items():
                for brand, details in brands.items():
                    new_filaments.append(Filament(
                        company_id=company_id, material=material, brand=brand, **details
                    ))
            if new_filaments:
                db_session.add_all(new_filaments)
            db_session.commit()
            return jsonify({"status": "saved"})
        except Exception as e:
            db_session.rollback()
            raise e
    else: # GET
        filaments_results = db_session.query(Filament).filter_by(company_id=company_id).all()
        filaments_dict = {}
        for f in filaments_results:
            if f.material not in filaments_dict:
                filaments_dict[f.material] = {}
            filaments_dict[f.material][f.brand] = {
                'price': f.price, 'stock_g': f.stock_g, 'efficiency_factor': f.efficiency_factor
            }
        return jsonify(filaments_dict)
