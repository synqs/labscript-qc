import json
import requests

session = requests.Session()
session.trust_env = False

url="http://127.0.0.1:8000/shots/config/"

#r = requests.post(url)
r = session.get(url)

#print(r.text)
print(r.content)
