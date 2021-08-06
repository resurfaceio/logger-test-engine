FROM resurfaceio/python:2.3.0
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "main.py" ]
