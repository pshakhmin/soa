import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:80")

settings = Settings()
