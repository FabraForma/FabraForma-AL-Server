from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict

class LoginModel(BaseModel):
    identifier: str
    password: str
    remember_me: bool = False

class RegisterCompanyModel(BaseModel):
    company_name: str
    admin_username: str
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)

class CreateUserModel(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str

class ChangePasswordModel(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class UpdateProfileModel(BaseModel):
    username: Optional[str] = None
    phone_number: Optional[str] = None
    dob: Optional[str] = None

class PrinterModel(BaseModel):
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
    price: float
    stock_g: float
    efficiency_factor: float = Field(..., ge=1.0)

class ProcessImageModel(BaseModel):
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
        allow_population_by_field_name = True

class QuotationPart(BaseModel):
    name: str
    cogs: float

class CompanyDetails(BaseModel):
    name: Optional[str]
    address: Optional[str]
    contact: Optional[str]
    logo_path: Optional[str]

class GenerateQuotationModel(BaseModel):
    customer_name: str
    customer_company: Optional[str]
    parts: List[QuotationPart]
    margin_percent: float
    tax_rate_percent: float
    company_details: CompanyDetails
