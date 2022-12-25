import os
import msgpack
import numpy as np
import time
import settings
from loguru import logger
import glob
import webbrowser
import time
import math

START_TIME = math.floor(time.time() * 1000)

def load_request(msg_path):
    with open(msg_path, "rb") as in_file:
        packet = msgpack.unpackb(in_file.read()[170:], strict_map_key=False)
    return packet

def load_response(msg_path):
    with open(msg_path, "rb") as in_file:
        packet = msgpack.unpackb(in_file.read(), strict_map_key=False)
    return packet

def create_gametora_helper_url(packet_data):
    if 'start_chara' not in packet_data:
        return None
    d = packet_data['start_chara']
    supports = d['support_card_ids'] + [d['friend_support_card_info']['support_card_id']]
    supports = list(map(str, supports))

    return f"https://gametora.com/umamusume/training-event-helper?deck={np.base_repr(int(str(d['card_id']) + str(d['scenario_id'])), 36)}-{np.base_repr(int(supports[0] + supports[1] + supports[2]), 36)}-{np.base_repr(int(supports[3] + supports[4] + supports[5]), 36)}".lower()


def process_message(message):
    message_time = int(str(os.path.basename(message))[:-9])
    if message_time < START_TIME:
        return

    logger.info(f"New Packet: {os.path.basename(message)}")

    if message.endswith("R.msgpack"):
        # Response
        data = load_response(message)
    else:
        # Request
        data = load_request(message)

        # Gametora
        if 'start_chara' in data:
            # Packet is a request to start a training
            webbrowser.open(create_gametora_helper_url(data), autoraise=True)

    os.remove(message)
    return


def get_msgpack_batch(msg_path):
    return sorted(glob.glob(os.path.join(msg_path, "*.msgpack")), key=os.path.getmtime)

def run():
    if not settings.get_tray_setting("Intercept packets"):
        return

    msg_path = settings.get("game_install_path")

    if not msg_path:
        logger.error("Packet intercept enabled but no carrotjuicer path found")
        return
    
    msg_path = os.path.join(msg_path, "CarrotJuicer")

    while True:
        if not settings.check_alive():
            return
        time.sleep(1)
        
        messages = get_msgpack_batch(msg_path)
        for message in messages:
            process_message(message)
