grouple recsys
==============================

aka Sagiri

Sagiri is a hikikomori anime illustrator. She reads such a lot manga and doujinshi so she can recommend something suitable for anyone. Like as this app will

Application allow grouple.co item recommendations. Regularly retrains, calculates items similarity and so on.

Web scrapper for collecting user bookmarks data included

Models:
 - implicit ALS for item recommendation
 - tSNE + Agglomerative clustering / DBSCAN for initial item recommendations


> sudo docker-compose -f docker-compose.yml up -d --build
> sudo docker-compose -f docker-compose-selflib.yml up -d --build

sudo docker-compose -f docker-compose.yml restart rumix

sudo docker-compose -f docker-compose.yml up -d -V --build --remove-orphans


### Single container update
```
docker-compose stop selflib
docker-compose build selflib
docker-compose up --no-start selflib
docker-compose start selflib
```