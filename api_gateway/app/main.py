import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users, promocodes # Import the new router
# from app.grpc_clients import close_grpc_channel # Optional: for graceful shutdown

# Configure logging (optional but recommended)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Gateway",
    description="API Gateway for microservices",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(promocodes.router, prefix="/api/v1/promocodes", tags=["Promocodes"])


# Optional: Add startup/shutdown events for resource management (like gRPC channel)
# @app.on_event("startup")
# async def startup_event():
#     logger.info("API Gateway starting up...")
#     # Initialize resources if needed

# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("API Gateway shutting down...")
#     await close_grpc_channel() # Close gRPC channel gracefully
