docker run --volume /home/iria/grouple/production/:/app/ \
           --volume /data/groupLe_recsys/processed:/data/groupLe_recsys/processed \
           -e CONFIG_FILE=mint_setting.yml \
           -p 5003:5000 \
           -d \
       sagiri