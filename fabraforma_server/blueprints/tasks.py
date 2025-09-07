import os
import json
from celery import shared_task
from flask import current_app

from fabraforma_server.database import db_session
from fabraforma_server.models import Printer, Filament
from fabraforma_server.server import (
    get_company_data_path, calculate_cogs_values, create_excel_file,
    log_to_master_excel, update_filament_stock, save_app_log
)

@shared_task
def process_verified_image(company_id, final_data, image_filename, image_bytes_b64):
    """
    Celery task to handle all post-verification processing for an image.
    """
    import base64
    image_bytes = base64.b64decode(image_bytes_b64)

    current_app.logger.info(f"CELERY_TASK: Starting processing for {final_data['Filename']}")

    # --- Save the image file ---
    image_dir = get_company_data_path(company_id, "local_log_images")
    new_filename = final_data["Filename"] + os.path.splitext(image_filename)[1]
    with open(os.path.join(image_dir, new_filename), 'wb') as f:
        f.write(image_bytes)

    # --- Fetch DB objects ---
    printer = db_session.query(Printer).filter_by(id=final_data.get("printer_id"), company_id=company_id).first()
    filament_model = db_session.query(Filament).filter_by(
        material=final_data.get("Material"),
        brand=final_data.get("Brand"),
        company_id=company_id
    ).first()

    if not printer or not filament_model:
        current_app.logger.error(f"CELERY_TASK: Critical data missing for {final_data['Filename']}. Aborting.")
        return {"status": "error", "message": "Printer or filament not found in DB."}

    printer_dict = {c.name: getattr(printer, c.name) for c in printer.__table__.columns}
    filament_dict = {c.name: getattr(filament_model, c.name) for c in filament_model.__table__.columns}

    # --- Perform calculations and file operations ---
    cogs = calculate_cogs_values(final_data, printer_dict, filament_dict)
    excel_path, excel_msg = create_excel_file(company_id, final_data, printer_dict, filament_dict)
    if not excel_path:
        current_app.logger.error(f"CELERY_TASK: Failed to create Excel log for {final_data['Filename']}: {excel_msg}")
        return {"status": "error", "message": f"Failed to create Excel log: {excel_msg}"}

    success, msg = log_to_master_excel(company_id, excel_path, final_data, cogs['user_cogs'], cogs['default_cogs'])
    if not success:
        current_app.logger.error(f"CELERY_TASK: Failed to update master log for {final_data['Filename']}: {msg}")
        return {"status": "error", "message": f"Failed to update master log: {msg}"}

    # --- Update database and logs ---
    update_filament_stock(company_id, final_data)
    save_app_log(company_id, final_data, cogs, new_filename)

    processed_log_path = get_company_data_path(company_id, "processed_log.json")
    try:
        processed_log = json.load(open(processed_log_path)) if os.path.exists(processed_log_path) else {}
        processed_log[image_filename] = "completed"
        with open(processed_log_path, 'w') as f:
            json.dump(processed_log, f, indent=2)
    except Exception as e:
        current_app.logger.error(f"CELERY_TASK: Failed to update processed_log.json for {image_filename}: {e}")

    current_app.logger.info(f"CELERY_TASK: Successfully processed and logged {final_data['Filename']}")
    return {"status": "success", "message": "File processed and logged successfully."}
