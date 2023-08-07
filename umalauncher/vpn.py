from loguru import logger
import requests
import time
import util
import os
import subprocess
import base64
import traceback
import random

def create_client(threader):
    vpn_radiobutton_status = threader.settings['s_vpn_client']

    if vpn_radiobutton_status['OpenVPN']:
        return OpenVPNClient(threader.settings['s_vpn_client_path'], threader.settings['s_vpn_ip_override'])
    elif vpn_radiobutton_status['NordVPN']:
        return NordVPNClient(threader.settings['s_vpn_client_path'])
    elif vpn_radiobutton_status['SoftEther']:
        return SoftEtherClient(threader.settings['s_vpn_ip_override'])

class VPNClient:
    def __init__(self, exe_path=""):
        self.exe_path = exe_path
        self.timeout = 30

    def _determine_vpngate_server(self):
        logger.info('Determining VPN server')

        r = requests.get('http://www.vpngate.net/api/iphone/', stream=True)
        r.raise_for_status()

        servers = []

        # lines = r.text.rstrip().split('\n')

        # for line in lines[2:-1]:
        #     line = line.rstrip().split(',')
        #     if line[6] == 'JP':
        #         servers.append(line)

        # if len(servers) == 0:
        #     logger.error('No Japanese VPN server found')
        #     util.show_warning_box('No Japanese VPN server found', 'No Japanese VPN server found.')
        #     return None, None
        
        # servers = sorted(servers, key=lambda x: int(x[2]), reverse=True)

        # logger.info(servers[0][1])
        # return servers[0][1], servers[0][14].rstrip()

        cur_chunk = ''

        for chunk in r.iter_content(chunk_size=1024):
            cur_chunk += chunk.decode('utf-8')
            split_chunk = cur_chunk.split('\n')
            for line in split_chunk[:-1]:
                server_data = line.split(',')
                if len(server_data) > 1 and server_data[6] == 'JP' and server_data[1].startswith('219.'):
                    logger.debug(server_data[1])
                    servers.append(server_data)
            cur_chunk = split_chunk[-1]

            if len(servers) >= 5:
                break

        if len(servers) > 0:
            # Randomly select a server
            server = random.choice(servers)
            logger.info(server[1])
            return server[1], server[14].rstrip()

        logger.error('No Japanese VPN server found')
        util.show_warning_box('No Japanese VPN server found', 'No Japanese VPN server found.')
        return None, None


    def _get_ip(self):
        ip = None
        url = 'https://api.myip.com/'
        url2 = 'https://api.ipify.org/?format=json'
        tries = 0
        while tries < 10:
            if tries > 5:
                url = url2
            try:
                ip = requests.get(url, timeout=10).json()['ip']
                break
            except:
                time.sleep(1)
                tries += 1
        logger.debug(ip)
        return ip
    
    def _after_ip_check(self):
        pass

    def _connect(self):
        pass

    def connect(self):
        before_ip = self._get_ip()
        try:
            success = self._connect()
        except Exception as e:
            logger.error(f'VPN connection failed: {e}')
            logger.error(traceback.format_exc())
            util.show_warning_box('VPN connection failed', 'VPN connection failed.<br>Check if your settings are correct. VPN client path must be set when using OpenVPN or NordVPN.<br>For more details on the issue, check the log.')
            self._disconnect()
            return False

        if not success:
            return False

        check_start_time = time.time()
        while time.time() - check_start_time < self.timeout:
            after_ip = self._get_ip()
            if before_ip != after_ip:
                break
            self._after_ip_check()
            time.sleep(2)

        if before_ip == after_ip:
            logger.error('VPN connection failed')
            util.show_warning_box('VPN connection failed', 'VPN connection failed')
            self._disconnect()
            return False
        
        logger.info('VPN connected')
        return True
    
    def _disconnect(self):
        pass

    def disconnect(self):
        self._disconnect()
        logger.info('VPN disconnected')


class NordVPNClient(VPNClient):
    def __init__(self, exe_path=""):
        super().__init__(exe_path)
        self.timeout = 30

    def _after_ip_check(self):
        self._connect()

    def _connect(self):
        if not os.path.exists(self.exe_path):
            logger.error('NordVPN executable not found')
            util.show_warning_box('NordVPN executable not found', 'NordVPN executable not found.<br>Please select the correct path in the preferences window.')
            return False
        
        logger.info('Connecting to NordVPN')
        subprocess.Popen([self.exe_path, "-c", "-g", "Japan"], creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(5)
        return True

    def _disconnect(self):
        logger.info('Disconnecting from NordVPN')
        subprocess.Popen([self.exe_path, "-d"], creationflags=subprocess.CREATE_NO_WINDOW)
        return True


class SoftEtherClient(VPNClient):
    def __init__(self, ip_override=""):
        super().__init__()
        self.ip_override = ip_override

    def _connect(self):
        if not self.ip_override:
            ip, _ = self._determine_vpngate_server()

            if not ip:
                return False
        else:
            ip = self.ip_override
            logger.info(f'Using IP override: {ip}')

        logger.info('Connecting to SoftEther')
        cmd_list = [
            r"vpncmd /CLIENT localhost /CMD AccountDisconnect uma_tmp",
            r"vpncmd /CLIENT localhost /CMD AccountDelete uma_tmp",
            f"vpncmd /CLIENT localhost /CMD AccountCreate uma_tmp /SERVER:{ip}:443 /USERNAME:vpn /HUB:VPNGATE /NICNAME:VPN",
            r"vpncmd /CLIENT localhost /CMD AccountStatusHide uma_tmp",
            r"vpncmd /CLIENT localhost /CMD AccountConnect uma_tmp"
        ]

        for cmd in cmd_list:
            subprocess.call(cmd, creationflags=subprocess.CREATE_NO_WINDOW)

        return True
    
    def _disconnect(self):
        logger.info('Disconnecting from SoftEther')
        subprocess.call(r"vpncmd /CLIENT localhost /CMD AccountDisconnect uma_tmp", creationflags=subprocess.CREATE_NO_WINDOW)
        return True

class OpenVPNClient(VPNClient):
    def __init__(self, exe_path="", profile_override=""):
        super().__init__(exe_path)
        self.ovpn_path = util.get_asset('vpn.ovpn')
        self.ovpn_process = None
        self.profile_override = profile_override

    def _connect(self):
        if not self.profile_override:
            _, ovpn = self._determine_vpngate_server()

            if not ovpn:
                return False
            
            logger.info('Connecting to OpenVPN')

            with open(self.ovpn_path, 'w', encoding='utf-8') as f:
                f.write(base64.b64decode(ovpn).decode('utf-8').replace("\ncipher ", "\n--data-ciphers "))

        else:
            self.ovpn_path = self.profile_override

        cmd = [self.exe_path, self.ovpn_path]
        
        self.ovpn_process = subprocess.Popen(cmd)

        return True

    def _disconnect(self):
        logger.info('Disconnecting from OpenVPN')
        if (not self.profile_override) and os.path.exists(self.ovpn_path):
            os.remove(self.ovpn_path)

        if self.ovpn_process:
            self.ovpn_process.kill()
            self.ovpn_process = None
        
        return True