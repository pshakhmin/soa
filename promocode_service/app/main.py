import logging
from app.grpc_server import serve # Import the serve function
from app.database import engine # Import engine to potentially check connection or run migrations
from app.models import Base # Import Base if you want to create tables on startup (dev only)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Promocode Service...")

    # Optional: Create database tables if they don't exist (useful for development)
    # In production, rely on Alembic migrations.
    # try:
    #     logger.info("Attempting to create database tables...")
    #     Base.metadata.create_all(bind=engine)
    #     logger.info("Database tables checked/created.")
    # except Exception as e:
    #     logger.error(f"Error creating database tables: {e}", exc_info=True)
        # Decide if you want to exit or continue if table creation fails

    # Start the gRPC server
    serve()

if __name__ == '__main__':
    main()
