#!/bin/bash
git pull
docker-compose build selflib
docker-compose stop selflib
docker-compose up --no-start selflib
docker-compose start selflib
