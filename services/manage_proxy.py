import socket
from services.utils import config
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
