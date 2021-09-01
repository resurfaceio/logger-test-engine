FROM resurfaceio/python:2.3.0
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt

CMD gunicorn --bind :$PORT main:app