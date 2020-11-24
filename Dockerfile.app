# base image contains the data
FROM mopd/crims-data:latest

WORKDIR /app

COPY crims /app/crims
COPY templates /app/templates
COPY server.py /app
COPY requirements.txt /app
COPY LICENSE /app

# ensure pip is up to date and install deps
RUN python -m pip install -U pip \
 && python -m pip install -r requirements.txt

# default flask port
EXPOSE 5000

ENV FLASK_APP=server.py

# https://stackoverflow.com/questions/30323224/deploying-a-minimal-flask-app-in-docker-server-connection-issues
CMD ["flask", "run", "--host", "0.0.0.0"]