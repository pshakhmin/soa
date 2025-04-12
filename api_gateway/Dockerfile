FROM python:3.10-slim

WORKDIR /code

COPY ./api_gateway/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy proto definitions from the promocode_service directory
# We copy them into a temporary location within the build context, e.g., /code/protos_src
COPY ./promocode_service/protos /code/protos_src

# Compile protos
# Ensure the output directory (/code/app) exists and is part of PYTHONPATH
# Update the include path (-I) and the input file path to use the correct source location
# This assumes the proto file is named 'promocode.proto' inside 'promocode_service/protos'

# Create the target directory for generated code and application code
RUN mkdir -p /code/app

# Compile protos first and output to /code/app
RUN python -m grpc_tools.protoc -I/code/protos_src --python_out=/code/app --grpc_python_out=/code/app /code/protos_src/promocode.proto

# Now copy the application code into /code/app
# This will place __init__.py, main.py, routes, etc., alongside the generated files
COPY ./api_gateway/app /code/app

# Ensure generated files have correct permissions if needed (usually not necessary)
# RUN chown -R <user>:<group> /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
