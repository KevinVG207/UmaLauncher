import os
import json
import gzip
from loguru import logger
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.backends.backend_qt5agg import FigureCanvas # pylint: disable=no-name-in-module
from matplotlib.figure import Figure
import gui


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
        logger.debug("Adding request.")
        request['_direction'] = 0

        # Remove keys that should not be saved
        for key in self.request_remove_keys:
            if key in request:
                del request[key]

        self.add_packet(request)


    def add_response(self, response: dict):
        logger.debug("Adding response.")
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


    def load_packets(self):
        packet_list = []
        logger.debug("Loading packets from file")
        if os.path.exists(self.get_sav_path()):
            with gzip.open(self.get_sav_path(), 'rb') as f:
                packet_list = json.loads(f"[{f.read().decode('utf-8')}]")
        logger.debug(f"Amount of packets loaded: {len(packet_list)}")
        return packet_list

    def analyze(self):
        app = TrainingAnalyzer(self)
        app.run(TrainingAnalyzerGui(app))
        app.close()


class TrainingAnalyzerGui(gui.UmaMainWidget):
    training_tracker = None

    def init_ui(self, *args, **kwargs):
        # Create widgets
        self.hello_world_label = qtw.QLabel("Hello World!")
        self.hello_world_label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        # Don't expand the label

        self.layout = qtw.QVBoxLayout(self)
        self.layout.addWidget(self.hello_world_label)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.layout.addWidget(self.canvas)

        ax = self.figure.subplots()

        self._parent.plot_stats(ax)


class TrainingAnalyzer(gui.UmaApp):
    training_tracker = None
    packets = None

    def __init__(self, training_tracker: TrainingTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.training_tracker = training_tracker
        self.packets = self.training_tracker.load_packets()


    def plot_stats(self, ax: plt.Axes):
        cur_turn = 0
        in_packets = []

        speed = []
        stamina = []
        power = []
        guts = []
        wisdom = []
        skill_points = []
        energy = []
        motivation = []
        fans = []


        def unpack_stats(packet: dict):
            speed.append(packet['chara_info']['speed'])
            stamina.append(packet['chara_info']['stamina'])
            power.append(packet['chara_info']['power'])
            guts.append(packet['chara_info']['guts'])
            wisdom.append(packet['chara_info']['wiz'])
            skill_points.append(packet['chara_info']['skill_point'])
            energy.append(packet['chara_info']['vital'])
            motivation.append(packet['chara_info']['motivation'])
            fans.append(packet['chara_info']['fans'])

        for packet in self.packets:
            if packet['_direction'] == 1:
                in_packets.append(packet)
                # Incoming packet
                chara_info = packet.get('chara_info')
                if chara_info is None:
                    continue
                turn = chara_info.get('turn')
                if not turn:
                    continue
                if turn > cur_turn:
                    cur_turn = turn
                    unpack_stats(packet)
        if len(in_packets) > 1:
            unpack_stats(in_packets[-1])
        # Plot
        x = list(range(1, len(speed) + 1))

        ax.plot(x, speed, label="Speed", color="#31B3FF")
        ax.plot(x, stamina, label="Stamina", color="#FF3F26")
        ax.plot(x, power, label="Power", color="#FFA217")
        ax.plot(x, guts, label="Guts", color="#FF72A5")
        ax.plot(x, wisdom, label="Wisdom", color="#10C88D")

        ax.legend()
        ax.set_xticks(x, minor=True)
        ax.set_xlim(1, len(speed))
        # Show all x-axis grid lines
        ax.xaxis.grid(True, which='both')
        # Make grid lines lighter
        ax.grid(color='#CCCCCC', linestyle='-', linewidth=1, alpha=0.5, which='both')
        # Make the y-axis show intervals of 100
        ax.yaxis.set_major_locator(ticker.MultipleLocator(100))



def main():
    TrainingTracker('2023_02_28_21_57_35').analyze()

if __name__ == "__main__":
    main()
