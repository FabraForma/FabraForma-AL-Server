"""
Pydantic models for API request validation.

This module defines the data structures and validation rules for the JSON
payloads expected by the various API endpoints. Using Pydantic ensures that
incoming data is well-formed before it is processed by the application logic.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict

class LoginModel(BaseModel):
    """Validator for the /auth/login endpoint."""
    identifier: str
    password: str
    remember_me: bool = False

class RegisterCompanyModel(BaseModel):
    """Validator for the /auth/register_company endpoint."""
    company_name: str
    admin_username: str
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)

class CreateUserModel(BaseModel):
    """Validator for the /auth/create_user endpoint."""
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str

class ChangePasswordModel(BaseModel):
    """Validator for the /user/change_password endpoint."""
    current_password: str
    new_password: str = Field(..., min_length=8)

class UpdateProfileModel(BaseModel):
    """Validator for the /user/profile endpoint."""
    username: Optional[str] = None
    phone_number: Optional[str] = None
    dob: Optional[str] = None

class PrinterModel(BaseModel):
    """Validator for printer objects sent to the /printers endpoint."""
    id: str
    brand: Optional[str]
    model: Optional[str]
    setup_cost: Optional[float]
    maintenance_cost: Optional[float]
    lifetime_years: Optional[int]
    power_w: Optional[float]
    price_kwh: Optional[float]
    buffer_factor: Optional[float] = Field(None, ge=1.0)
    uptime_percent: Optional[float] = Field(None, ge=0, le=100)

class FilamentsPostModel(BaseModel):
    """Validator for the filament details within the /filaments endpoint payload."""
    price: float
    stock_g: float
    efficiency_factor: float = Field(..., ge=1.0)

class ProcessImageModel(BaseModel):
    """Validator for the data sent to the /process_image endpoint."""
    Filename: str
    Date: str
    Printer: str
    Material: str
    Brand: str
    Filament_Cost_kg: float = Field(..., alias='Filament Cost (₹/kg)')
    Filament_g: float = Field(..., alias='Filament (g)')
    Time_str: str = Field(..., alias='Time (e.g. 7h 30m)')
    Labour_Time_min: float = Field(..., alias='Labour Time (min)')
    Labour_Rate_hr: float = Field(..., alias='Labour Rate (₹/hr)')
    printer_id: str
    timestamp: str

    class Config:
        # Allow the model to be populated by field name OR alias.
        allow_population_by_field_name = True

class CompanyDetails(BaseModel):
    """Validator for company details used in quotations."""
    name: Optional[str]
    address: Optional[str]
    contact: Optional[str]
    logo_path: Optional[str]

class GenerateQuotationModel(BaseModel):
    """Validator for the /generate_quotation endpoint."""
    customer_name: str
    customer_company: Optional[str]
    parts: List[Dict] # A simple dict is sufficient here
    margin_percent: float
    tax_rate_percent: float
    company_details: CompanyDetails
