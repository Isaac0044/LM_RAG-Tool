import requests
import json

# define API
url = "http://localhost:11434/api/generate"

# define data
data = {
    "model": "qwen2.5",
    "prompt": "Why is the sky blue?",
    "stream": False,
    "options": {
       
    }
}

# sand POST
try:
    response = requests.post(url, json=data)
    # check response
    if response.status_code == 200:
        print("Response:", response.json())
    else:
        print(f"Error: {response.status_code}, {response.text}")
except requests.exceptions.RequestException as e:
    print("Request failed:", e)
