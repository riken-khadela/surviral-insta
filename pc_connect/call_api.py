import requests
import json

url = "http://localhost:8000/api/run-command/"

def call_api():
    
    payload = json.dumps({
    "cmd": ""
    })

    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

while True :
    call_api()