from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict

# --- AUTHENTICATION & USER MANAGEMENT ---

class LoginModel(BaseModel):
    identifier: str
    password: str
    remember_me: bool = False

class RegisterCompanyModel(BaseModel):
    company_name: str = Field(..., min_length=1)
    admin_username: str = Field(..., min_length=3)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)

class CreateUserModel(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str

    @validator('role')
    def role_must_be_valid(cls, v):
        if v not in ['admin', 'user']:
            raise ValueError("Role must be either 'admin' or 'user'")
        return v

class ChangePasswordModel(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class UpdateProfileModel(BaseModel):
    username: Optional[str] = Field(None, min_length=3)
    phone_number: Optional[str] = None
    dob: Optional[str] = None # Basic validation, can be improved with date parsing

# --- DATA MANAGEMENT ---

class PrinterModel(BaseModel):
    id: str
    brand: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    setup_cost: float = Field(..., ge=0)
    maintenance_cost: float = Field(..., ge=0)
    lifetime_years: int = Field(..., ge=1)
    power_w: float = Field(..., ge=0)
    price_kwh: float = Field(..., ge=0)
    buffer_factor: float = Field(..., ge=1.0)
    uptime_percent: float = Field(..., ge=0, le=100)

class FilamentsPostModel(BaseModel):
    price: float = Field(..., ge=0)
    stock_g: float = Field(..., ge=0)
    efficiency_factor: float = Field(..., gt=0)

# --- CORE LOGIC ---

class ProcessImageModel(BaseModel):
    filename: str = Field(..., min_length=1, alias='Filename')
    filament_g: float = Field(..., ge=0, alias='Filament (g)')
    time_str: str = Field(..., min_length=1, alias='Time (e.g. 7h 30m)')
    timestamp: str # ISO 8601 format
    printer_id: str
    printer_name: str = Field(..., alias='Printer')
    material: str = Field(..., alias='Material')
    brand: str = Field(..., alias='Brand')
    filament_cost_kg: float = Field(..., ge=0, alias='Filament Cost (₹/kg)')
    labour_time_min: int = Field(..., ge=0, alias='Labour Time (min)')
    labour_rate_hr: float = Field(..., ge=0, alias='Labour Rate (₹/hr)')

    class Config:
        allow_population_by_field_name = True

class QuotationPartModel(BaseModel):
    name: str
    cogs: float = Field(..., ge=0)

class CompanyDetailsModel(BaseModel):
    name: str
    address: str
    contact: str
    logo_path: Optional[str] = None

class GenerateQuotationModel(BaseModel):
    customer_name: str = Field(..., min_length=1)
    customer_company: Optional[str] = None
    parts: List[QuotationPartModel]
    margin_percent: float = Field(..., ge=0)
    tax_rate_percent: float = Field(..., ge=0)
    company_details: CompanyDetailsModel

