FROM python:3.6

RUN mkdir -p /app
WORKDIR /app
COPY requirements.txt /app/

RUN apt update -y && apt upgrade -y
RUN apt install -y python3-pip
RUN pip3 install -r /app/requirements.txt

COPY start_docker.sh /app/start_docker.sh
RUN chmod +x /app/start_docker.sh

EXPOSE 5000

CMD ["/bin/bash", "/app/start_docker.sh"]