from loguru import logger
import requests
import time
import util
import os
import subprocess
import base64
import traceback
import random

def create_client(threader, cygames=False):
    vpn_radiobutton_status = threader.settings['s_vpn_client']

    if vpn_radiobutton_status['OpenVPN']:
        return OpenVPNClient(threader, threader.settings['s_vpn_client_path'], threader.settings['s_vpn_ip_override'], cygames)
    elif vpn_radiobutton_status['NordVPN']:
        return NordVPNClient(threader, threader.settings['s_vpn_client_path'])
    elif vpn_radiobutton_status['SoftEther']:
        return SoftEtherClient(threader, threader.settings['s_vpn_ip_override'], cygames)

class VPNClient:
    def __init__(self, threader, exe_path=""):
        self.threader = threader
        self.exe_path = exe_path
        self.timeout = 30

    def _determine_vpngate_server(self, cygames=False):
        logger.info('Requesting VPN server list from Umapyoi.net')

        vpn_type = 'cygames' if cygames else 'dmm'

        logger.info(f"Type: {vpn_type}")

        r = requests.get(f'https://umapyoi.net/api/v1/vpn/{vpn_type}')
        r.raise_for_status()

        servers = r.json()
        if servers:
            return servers[0]['_profile']

        logger.error('No VPN server found')
        util.show_warning_box('No VPN server found', 'No VPN server found.<br>Please try again later.')
        return None


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
        return ip
    
    def _after_ip_check(self):
        pass

    def _connect(self):
        pass

    def connect(self):
        self.threader.tray.set_connecting()
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
            self._disconnect()
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
            util.show_warning_box('VPN connection failed', 'VPN connection failed.<br>Check if your settings are correct.')
            self._disconnect()
            return False
        
        logger.info('VPN connected')
        time.sleep(4)
        self.threader.tray.set_connected()
        return True
    
    def _disconnect(self):
        pass

    def disconnect(self):
        self._disconnect()
        self.threader.tray.reset_status()
        logger.info('VPN disconnected')


class NordVPNClient(VPNClient):
    def __init__(self, threader, exe_path=""):
        super().__init__(threader, exe_path)
        self.timeout = 60

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
        subprocess.call([self.exe_path, "-d"], creationflags=subprocess.CREATE_NO_WINDOW)
        return True


class SoftEtherClient(VPNClient):
    def __init__(self, threader, ip_override="", cygames=False):
        super().__init__(threader)
        self.ip_override = ip_override
        self.cygames = cygames

    def _connect(self):
        ip = ""

        if not self.ip_override:
            ovpn_config = self._determine_vpngate_server(cygames=self.cygames)

            if not ovpn_config:
                return False
            
            for line in ovpn_config.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and line.startswith("remote "):
                    _, ip, port = line.split(" ", 2)
                    ip = f"{ip}:{port}"
                    break

            if not ip:
                util.show_warning_box('VPN connection failed', 'VPN connection failed.<br>The fetched OpenVPN config does not have a remote IP.')
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
    def __init__(self, threader, exe_path="", profile_override="", cygames=False):
        super().__init__(threader, exe_path)
        self.ovpn_path = util.get_asset('vpn.ovpn')
        self.ovpn_process = None
        self.profile_override = profile_override
        self.cygames = cygames

    def _connect(self):
        if not self.profile_override:
            ovpn = self._determine_vpngate_server(cygames=self.cygames)

            if not ovpn:
                return False
            
            logger.info('Connecting to OpenVPN')

            with open(self.ovpn_path, 'w', encoding='utf-8') as f:
                f.write(ovpn)

        else:
            self.ovpn_path = self.profile_override

        cmd = [self.exe_path, self.ovpn_path]
        
        self.ovpn_process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)

        return True

    def _disconnect(self):
        logger.info('Disconnecting from OpenVPN')
        if (not self.profile_override) and os.path.exists(self.ovpn_path):
            os.remove(self.ovpn_path)

        if self.ovpn_process:
            self.ovpn_process.kill()
            self.ovpn_process = None
        
        return True