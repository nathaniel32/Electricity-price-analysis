import json
from types import SimpleNamespace
import requests

def check_ip():
    url = 'https://api.ipify.org?format=json'
    response = requests.get(url, proxies=load_config().PROXIES)
    print(response.text)

def load_config(path: str = "config.json") -> SimpleNamespace:
    with open(path, "r") as file:
        data = json.load(file)
        return SimpleNamespace(**data)
    
config = load_config()