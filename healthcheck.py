import requests as r

resp = r.get('http://0.0.0.0:5000/healthcheck')
if resp.status_code != 200:
    exit(1)
if resp.json()['status'] != "UP":
    exit(1)
