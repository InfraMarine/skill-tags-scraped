import requests

responce = requests.get("http://127.0.0.1:5000/tag/2?top=1")
print(responce.json())