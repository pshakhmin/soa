from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings  # Import settings from promocode_service config

# Create the SQLAlchemy engine using the DATABASE_URL from settings
# Example: postgresql://promo_user:promo_password@promocode-db:5432/promocode_db
engine = create_engine(settings.DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative class definitions
# Note: It's generally better to import Base from models.py to avoid circular imports
# if models need the engine or session. However, for simple setup, defining it here
# or importing from models is acceptable. Let's assume models.py defines its own Base.
# from app.models import Base # Preferred way if models.py defines Base

# If models.py does *not* define Base, uncomment the line below
# Base = declarative_base()


# Dependency to get DB session
def get_db():
    """
    Dependency function that yields a SQLAlchemy session.
    Ensures the session is always closed afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
