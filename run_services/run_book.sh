docker run --volume /home/iria/grouple/production/:/app/ \
           --volume /data/groupLe_recsys/processed:/data/groupLe_recsys/processed \
           -e CONFIG_FILE=book_setting.yml \
           -d \
       sagiri