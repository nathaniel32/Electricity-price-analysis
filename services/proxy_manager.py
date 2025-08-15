from services.utils import config
import requests
import socket

class ProxyManager:
    def __init__(self):
        pass
 
    def check_ip(self):
        url = config.IP_CHECK_URL
        proxies = config.PROXIES if config.USE_PROXY else None
        response = requests.get(url, proxies=proxies)
        print(response.text)

    def send_signal_newnym(self, password=None):
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