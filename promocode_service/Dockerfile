# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Generate gRPC code (optional, can be done locally and copied)
# Ensure proto files are copied first if running this step
# RUN python -m grpc_tools.protoc -I./proto --python_out=./app --pyi_out=./app --grpc_python_out=./app ./proto/promocode.proto

# Expose port (Port is defined by env var PROMOCODE_GRPC_PORT, so EXPOSE is optional here)
# EXPOSE 50052

# Command to run the application
CMD ["python", "app/main.py"] # Runs the gRPC server defined in main.py
