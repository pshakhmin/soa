FROM python:3.10-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy proto definitions
COPY ./protos /code/protos

# Compile protos
# Ensure the output directory (/code/app) exists and is part of PYTHONPATH
# The '.' path for proto_path assumes promocode.proto might import other protos from the ./protos root
RUN python -m grpc_tools.protoc -I./protos --python_out=./app --grpc_python_out=./app ./protos/promocode.proto

COPY ./app /code/app

# Ensure generated files have correct permissions if needed (usually not necessary)
# RUN chown -R <user>:<group> /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
