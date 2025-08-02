import json
from types import SimpleNamespace
import requests

def check_ip():
    url = config.IP_CHECK_URL
    proxies = config.PROXIES if config.USE_PROXY else None
    response = requests.get(url, proxies=proxies)
    print(response.text)

def load_config(path: str = "config.json") -> SimpleNamespace:
    with open(path, "r") as file:
        data = json.load(file)
        return SimpleNamespace(**data)
    
config = load_config()