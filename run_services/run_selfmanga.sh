docker run --volume $(pwd)/../recommendations_server:/recommendations_server \
           --volume /data/groupLe_recsys/processed:/data/groupLe_recsys/processed \
           -p 5013:5000 \
           -e CONFIG_FILE=selfmanga_setting.yml \
           -d \
       sagiri