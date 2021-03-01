import json
import requests

session = requests.Session()
session.trust_env = False

#payload = {'idle_time': 0.5, 'shots': 5, 'user_id':'rohitp'}
payload = {
    'experiment_0': {
        'instructions': [
            ('rx', [0], [0.7]),
            ('delay', [0, 1], [20]),
            ('measure', [0], []),
            ('measure', [1], [])
        ],
        'num_wires': 2,
        'shots': 2
    },
    'user_id':'rohitp'
 }
url="http://127.0.0.1:8000/shots/upload/"

#r = requests.post(url, data={'json':json.dumps(payload)})
r = session.post(url, data={'json':json.dumps(payload)})

print(r.text)
