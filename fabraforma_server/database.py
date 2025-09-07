import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

# Load environment variables from .env file, so this module is self-contained
load_dotenv()

# Get the database URL from environment variables, defaulting to the local sqlite file
DATABASE_URL = os.environ.get("DATABASE_URI", "sqlite:///server_data.sqlite")

# The engine is the starting point for any SQLAlchemy application.
# It's the low-level object that handles communication with the database.
engine = create_engine(DATABASE_URL)

# A sessionmaker object is a factory for creating new Session objects.
# We configure it once and can then create sessions from it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# To make session management easier in a web context, we use a scoped_session.
# This provides a registry of Session objects that are thread-local, meaning
# each thread (and thus each request) gets its own session.
db_session = scoped_session(SessionLocal)

def init_db_orm():
    """
    This function can be used to create the database tables, but we
    will primarily rely on Alembic for migrations.
    """
    from models import Base
    print("Initializing database with SQLAlchemy ORM...")
    # This command creates tables based on the models.
    # It's useful for initial setup in environments without Alembic.
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")
