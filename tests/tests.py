import unittest
import sys
import glob
import json
import traceback
sys.path.append("../umalauncher")

import os
os.chdir("../umalauncher")

import time
import threading

import threader

from loguru import logger

THREADER = None
THREADER_THREAD = None

def setup():
    global THREADER
    global THREADER_THREAD

    THREADER = threader.Threader(test_mode=True)
    THREADER_THREAD = threading.Thread(target=THREADER.run, name="Threader")
    THREADER_THREAD.start()

    logger.remove()
    logger.add(sys.stderr, level="WARNING")

def cleanup():
    global THREADER
    global THREADER_THREAD

    THREADER.stop()
    THREADER_THREAD.join()
    threader.cleanup()

class ThreaderTester(unittest.TestCase):
    def test_threader(self):
        self.assertTrue(isinstance(THREADER, threader.Threader))

class PacketTester(unittest.TestCase):
    def __init__(self, name, packet_name=None):
        super().__init__(name)
        self.packet_name = packet_name

    def test_packet(self):
        print(f"Testing packet {self.packet_name}")
        packet_path = "../tests/packets/" + self.packet_name
        with open(packet_path, "r", encoding='utf-8') as f:
            packet = json.load(f)

        try:
            if self.packet_name.startswith("out_"):
                THREADER.carrotjuicer.handle_request(packet)
            else:
                THREADER.carrotjuicer.handle_response(packet)
            self.assertTrue(True)
        except Exception as e:
            self.assertTrue(False, msg=f"Failed to handle packet {self.packet_name}")
            print(e)
            print(traceback.format_exc())

if __name__ == '__main__':
    setup()
    runner = unittest.TextTestRunner(verbosity=2)

    suite = unittest.TestSuite()

    # Generic
    suite.addTest(ThreaderTester("test_threader"))
    
    # Packets
    # TODO: Add expected rich presence checks
    suite.addTest(PacketTester("test_packet", "out_default.json"))
    suite.addTest(PacketTester("test_packet", "in_home_screen_from_title_screen.json"))
    suite.addTest(PacketTester("test_packet", "in_enter_gacha_screen.json"))
    suite.addTest(PacketTester("test_packet", "out_theater_start_watching_umapyoi.json"))
    suite.addTest(PacketTester("test_packet", "in_theater_start_watching_umapyoi.json"))
    suite.addTest(PacketTester("test_packet", "in_theater_enter_theater.json"))
    suite.addTest(PacketTester("test_packet", "in_ura_continue_from_home.json"))
    suite.addTest(PacketTester("test_packet", "out_ura_guts_training.json"))
    suite.addTest(PacketTester("test_packet", "in_ura_guts_training.json"))
    suite.addTest(PacketTester("test_packet", "out_ura_event_no_choices.json"))
    suite.addTest(PacketTester("test_packet", "in_ura_event_no_choices.json"))

    runner.run(suite)
    cleanup()