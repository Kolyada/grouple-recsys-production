FROM python:3.6

RUN mkdir -p /app
RUN mkdir /app/logs
WORKDIR /app

RUN apt update -y && apt upgrade -y
RUN apt install -y python3-pip
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

COPY *.sh /app/
RUN chmod +x /app/start_docker.sh

COPY database /app/database
COPY models /app/models
COPY http_utils /app/http_utils
COPY server.py /app/server.py

EXPOSE 5000
CMD ["/bin/bash", "./start_docker.sh"]
