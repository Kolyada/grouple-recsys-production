# Deploy

## Installation

- Move user-item-rate data to `data/processed/{site_name}/views.csv`
- Move exploration recs data to `data/processed/{site_name}/explorational_recs.json`
- Check configs and `models/implicitALS_cfgs/`


## Run

For custom service container
```
./build_docker.sh
./run_docker.sh {port} {config_file_name}
```

For default services
```
cd run_services
./run_{service}.sh
```
