docker run --volume /home/iria/grouple/production/:/app/ \
           --volume /data/groupLe_recsys/processed:/data/groupLe_recsys/processed \
           -e CONFIG_FILE=manga_setting.yml \
           -p 5002:5000 \
           -d \
       sagiri