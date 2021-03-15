FROM python:3.6

RUN mkdir -p /app
RUN mkdir /app/logs
WORKDIR /app

COPY database /app/database
COPY models /app/models
COPY server.py /app/server.py

COPY *.sh /app/
RUN chmod +x /app/start_docker.sh

COPY requirements.txt /app/
RUN apt update -y && apt upgrade -y
RUN apt install -y python3-pip
RUN pip3 install -r /app/requirements.txt

EXPOSE 5000
CMD ["/bin/bash", "./start_docker.sh"]
