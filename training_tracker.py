import os
import json
import gzip
from loguru import logger
import PyQt5.QtCore as qtc
from PyQt5 import QtGui
import PyQt5.QtWidgets as qtw
import util


class TrainingTracker():
    training_log_folder = None
    training_id = None
    previous_packet = None

    request_remove_keys = [
        "viewer_id",
        "device",
        "device_id",
        "device_name",
        "graphics_device_name",
        "ip_address",
        "platform_os_version",
        "carrier",
        "keychain",
        "locale",
        "button_info",
        "dmm_viewer_id",
        "dmm_onetime_token",
    ]


    def __init__(self, training_id: str, training_log_folder: str="training_logs"):
        self.previous_packet = None

        self.training_log_folder = training_log_folder

        # Create training_logs folder if it doesn't exist.
        if not os.path.exists(self.training_log_folder):
            os.makedirs(self.training_log_folder)

        self.training_id = self.make_training_id_safe(training_id)


    def make_training_id_safe(self, training_id: str):
        def convert_char(c: str):
            if c.isalnum():
                return c
            return "_"
        return "".join(convert_char(c) for c in training_id)


    def training_id_matches(self, training_id: str):
        return self.make_training_id_safe(training_id) == self.training_id


    def add_packet(self, packet: dict):
        self.write_previous_packet()
        self.previous_packet = packet


    def add_request(self, request: dict):
        request['_direction'] = 0

        # Remove keys that should not be saved
        for key in self.request_remove_keys:
            if key in request:
                del request[key]

        self.add_packet(request)


    def add_response(self, response: dict):
        response['_direction'] = 1
        self.add_packet(response)


    def get_sav_path(self):
        return str(os.path.join(self.training_log_folder, self.training_id)) + ".gz"


    def write_previous_packet(self):
        # Convert to json string and save with gzip
        # Append to gzip if file exists
        is_first = not os.path.exists(self.get_sav_path())
        if self.previous_packet is not None:
            with gzip.open(self.get_sav_path(), 'ab') as f:
                if not is_first:
                    f.write(','.encode('utf-8'))
                f.write(json.dumps(self.previous_packet, ensure_ascii=False).encode('utf-8'))


    def unpickle_packets(self):
        packet_list = []
        logger.debug("Loading packets from file")
        if os.path.exists(self.get_sav_path()):
            with gzip.open(self.get_sav_path(), 'rb') as f:
                packet_list = json.loads(f"[{f.read().decode('utf-8')}]")
        logger.debug(f"Amount of packets loaded: {len(packet_list)}")
        return packet_list

    def analyze(self):
        TrainingAnalyzer(self)


class TrainingAnalyzerGui(qtw.QWidget):
    training_tracker = None
    def __init__(self, training_tracker: TrainingTracker):
        super().__init__()
        self.training_tracker = training_tracker

        # Set window icon
        self.setWindowIcon(QtGui.QIcon(util.get_asset('favicon.ico')))
        self.setWindowTitle("Training Analyzer")

        # Set window size
        self.resize(800, 600)

        # Disallow resizing
        self.setFixedSize(self.size())

        # Center widget to primary screen
        screen = qtw.QDesktopWidget().primaryScreen()
        screen_size = qtw.QDesktopWidget().screenGeometry(screen)
        self.move(screen_size.center() - self.rect().center())

        # Hide maxminize and minimize buttons
        self.setWindowFlag(qtc.Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(qtc.Qt.WindowType.WindowMinimizeButtonHint, False)

        # Create widgets
        self.hello_world_label = qtw.QLabel("Hello World!")
        self.hello_world_label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)

        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.hello_world_label)

        # Bring to foreground
        self.raise_()

        # Stay on top
        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)



class TrainingAnalyzer():
    training_tracker = None
    app = None

    def __init__(self, training_tracker: TrainingTracker):
        self.training_tracker = training_tracker

        app = qtw.QApplication([])
        gui = TrainingAnalyzerGui(self.training_tracker)
        gui.show()
        app.exec_()


def main():
    TrainingTracker('2023_02_28_21_57_35').analyze()

if __name__ == "__main__":
    main()
