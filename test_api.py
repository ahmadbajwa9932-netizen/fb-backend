import requests

url = "http://127.0.0.1:5000/api/download"
data = {"url": "https://www.facebook.com/share/v/17KW4y8Dun/"}

res = requests.post(url, json=data)
print(res.json())
