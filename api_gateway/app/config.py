import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:80")
    PROMOCODE_SERVICE_GRPC_URL: str = os.getenv("PROMOCODE_SERVICE_GRPC_URL", "promocode-service:50052")

settings = Settings()
