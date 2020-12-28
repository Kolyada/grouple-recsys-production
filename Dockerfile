FROM python:3.6

RUN mkdir /recommendations_server
COPY ./recommendations_server/requirements.txt /recommendations_server/requirements.txt

RUN apt update -y && apt upgrade -y
RUN apt install -y python3-pip
RUN pip3 install -r /recommendations_server/requirements.txt

COPY ./start_docker.sh /start_docker.sh
RUN chmod +x ./start_docker.sh

CMD ["/bin/bash", "./start_docker.sh"]