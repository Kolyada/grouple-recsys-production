docker run --volume /home/iria/grouple/production/recommendations_server:/recommendations_server \
           --volume /data/groupLe_recsys/processed:/data/groupLe_recsys/processed \
           -p 5002:5000 \
           -e CONFIG_FILE=manga_setting.yml \
       sagiri