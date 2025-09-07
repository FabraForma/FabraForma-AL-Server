from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    users = relationship("User", back_populates="company")
    printers = relationship("Printer", back_populates="company")
    filaments = relationship("Filament", back_populates="company")

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    company_id = Column(String, ForeignKey('companies.id'), nullable=False)
    role = Column(String, nullable=False)
    phone_number = Column(String)
    dob = Column(String)
    profile_picture_path = Column(String)

    company = relationship("Company", back_populates="users")
    auth_tokens = relationship("AuthToken", back_populates="user")

    __table_args__ = (UniqueConstraint('username', 'company_id', name='_username_company_uc'),)

class Printer(Base):
    __tablename__ = 'printers'
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey('companies.id'), nullable=False)
    brand = Column(String)
    model = Column(String)
    setup_cost = Column(Float)
    maintenance_cost = Column(Float)
    lifetime_years = Column(Integer)
    power_w = Column(Float)
    price_kwh = Column(Float)
    buffer_factor = Column(Float)
    uptime_percent = Column(Float)

    company = relationship("Company", back_populates="printers")

class Filament(Base):
    __tablename__ = 'filaments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String, ForeignKey('companies.id'), nullable=False)
    material = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    price = Column(Float)
    stock_g = Column(Float)
    efficiency_factor = Column(Float)

    company = relationship("Company", back_populates="filaments")

    __table_args__ = (UniqueConstraint('company_id', 'material', 'brand', name='_company_material_brand_uc'),)

class AuthToken(Base):
    __tablename__ = 'auth_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    token_hash = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)

    user = relationship("User", back_populates="auth_tokens")
