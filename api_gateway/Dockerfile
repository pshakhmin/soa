FROM python:3.10-slim

WORKDIR /code

COPY ./api_gateway/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./promocode_service/protos /code/protos_src

RUN mkdir /code/app

RUN python -m grpc_tools.protoc -I/code/protos_src --python_out=/code/app --grpc_python_out=/code/app /code/protos_src/promocode.proto

COPY ./api_gateway/app /code/app

# RUN chown -R <user>:<group> /code/app
#
#CMD ["ls", "/code/./app", "/code/app"]
#
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
