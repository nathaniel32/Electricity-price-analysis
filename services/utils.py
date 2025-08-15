import json
from types import SimpleNamespace
import requests
import hashlib
import socket

def check_ip():
    url = config.IP_CHECK_URL
    proxies = config.PROXIES if config.USE_PROXY else None
    response = requests.get(url, proxies=proxies)
    print(response.text)

def send_signal_newnym(password=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((config.PROXY_SETTING_IP, config.PROXY_SETTING_PORT))

    def send_cmd(cmd):
        s.send((cmd + '\r\n').encode())
        return s.recv(1024).decode()

    if password:
        resp = send_cmd(f'AUTHENTICATE "{password}"')
    else:
        resp = send_cmd('AUTHENTICATE')

    if '250 OK' not in resp:
        print('Authentication failed:', resp)
        s.close()
        return False

    resp = send_cmd('SIGNAL NEWNYM')
    if '250 OK' in resp:
        print('circuit changed')
        s.close()
        return True
    else:
        print('Failed to change circuit:', resp)
        s.close()
        return False

def load_config(path: str = "config.json") -> SimpleNamespace:
    with open(path, "r") as file:
        data = json.load(file)
        return SimpleNamespace(**data)
    
def md5_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()
    
config = load_config()