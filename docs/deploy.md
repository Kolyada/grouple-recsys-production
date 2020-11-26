# Deploy

## Installation

- Install libs `pip3 install -r requirements.txt`
- Move viewes data to `data/processed/{site_name}/views.csv`
- Move exploration recs data to `data/processed/{site_name}/explorational_recs.json`
- Check configs and `models/implicitALS_cfgs/`


## Run

```
cd models
python3 service.py implicitALS_cfgs/{site_name}.yml
```

To run the process in background use

`nohup command &`