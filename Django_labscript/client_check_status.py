import json
import requests

session = requests.Session()
session.trust_env = False

payload = {'job_id': '20210212_122519_1f5eb'}
url="http://127.0.0.1:8000/shots/check_shot_status/"

#r = requests.post(url, data={'json':json.dumps(payload)})
r = session.post(url, data={'json':json.dumps(payload)})

print(r.text)
