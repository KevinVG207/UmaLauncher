import os
import json
import gzip
import re
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.backends.backend_qt5agg import FigureCanvas # pylint: disable=no-name-in-module
from matplotlib.figure import Figure
import gui
import mdb
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


class ActionType(Enum):
    Unknown = -1
    Start = 0
    End = 1
    Training = 2
    Event = 3
    Race = 4
    SkillHint = 5

class CommandType(Enum):
    Speed = 101
    Stamina = 105
    Power = 102
    Guts = 103
    Wisdom = 106

@dataclass
class TrainingAction():
    """Represents a single training action.
    d = delta.
    """
    scenario_id: int
    turn: int
    speed: int
    stamina: int
    power: int
    guts: int
    wisdom: int
    skill_pt: int
    energy: int
    motivation: int
    fans: int
    skill: set
    skillhint: set
    status: set

    action_type: ActionType = ActionType.Unknown
    text: str = ''
    dspeed: int = 0
    dstamina: int = 0
    dpower: int = 0
    dguts: int = 0
    dwisdom: int = 0
    dskill_pt: int = 0
    denergy: int = 0
    dmotivation: int = 0
    dfans: int = 0
    add_skill: set = field(default_factory=set)
    remove_skill: set = field(default_factory=set)
    add_skillhint: set = field(default_factory=set)
    remove_skillhint: set = field(default_factory=set)
    add_status: set = field(default_factory=set)
    remove_status: set = field(default_factory=set)


class TrainingAnalyzer(gui.UmaApp):
    training_tracker = None
    packets = None
    chara_names_dict = util.get_character_name_dict()

    def __init__(self, training_tracker: TrainingTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.training_tracker = training_tracker
        self.packets = self.training_tracker.load_packets()
        self.to_csv()


    def to_csv(self):
        action_list = []
        
        # Grab req/resp pairs
        prev_resp = None
        for i in range(0, len(self.packets), 2):
            req = self.packets[i]
            resp = self.packets[i+1]

            chara_info = resp['chara_info']

            # Create base action
            action = TrainingAction(
                scenario_id=chara_info['scenario_id'],
                turn=chara_info['turn'],
                speed=chara_info['speed'],
                stamina=chara_info['stamina'],
                power=chara_info['power'],
                guts=chara_info['guts'],
                wisdom=chara_info['wiz'],
                skill_pt=chara_info['skill_point'],
                energy=chara_info['vital'],
                motivation=chara_info['motivation'],
                fans=chara_info['fans'],
                skill=set(tuple(item) for item in chara_info['skill_array']),
                skillhint=set(tuple(item) for item in chara_info['skill_tips_array']),
                status=set(chara_info['chara_effect_id_array'])
            )

            # Calculate deltas
            if action_list:
                prev_action = action_list[-1]
                action.dspeed = action.speed - prev_action.speed
                action.dstamina = action.stamina - prev_action.stamina
                action.dpower = action.power - prev_action.power
                action.dguts = action.guts - prev_action.guts
                action.dwisdom = action.wisdom - prev_action.wisdom
                action.dskill_pt = action.skill_pt - prev_action.skill_pt
                action.denergy = action.energy - prev_action.energy
                action.dmotivation = action.motivation - prev_action.motivation
                action.dfans = action.fans - prev_action.fans
                action.add_skill = action.skill - prev_action.skill
                action.remove_skill = prev_action.skill - action.skill
                action.add_skillhint = action.skillhint - prev_action.skillhint
                action.remove_skillhint = prev_action.skillhint - action.skillhint
                action.add_status = action.status - prev_action.status
                action.remove_status = prev_action.status - action.status


            # Determine action type
            self.determine_action_type(req, resp, action, prev_resp)

            # Add to list
            action_list.append(action)

            prev_resp = resp
        return

    def determine_action_type(self, req: dict, resp: dict, action: TrainingAction, prev_resp: dict):

        # Start of run
        if 'start_chara' in req:
            action.action_type = ActionType.Start
            return

        # Event requested by client
        if 'event_id' in req:
            story_id = prev_resp['unchecked_event_array'][0]['story_id']

            # If story_id matches regex with group
            match = re.match(r'80(\d{4})003', str(story_id))
            if match:
                # Skill hint
                action.action_type = ActionType.SkillHint
                action.text = self.chara_names_dict[int(match.group(1))]
                action.action_type = ActionType.SkillHint
                return

            action.action_type = ActionType.Event
            # This is assuming there is only ever one event in unchecked_event_array.
            action.text = mdb.get_event_title(story_id)
            return
        
        if 'command_type' in req:
            if str(req['command_id'])[0] == '1':
                # Training
                action.action_type = ActionType.Training
                action.text = CommandType(req['command_id']).name
                return
        
        return


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
    TrainingTracker('2023_03_03_00_13_55').analyze()

if __name__ == "__main__":
    main()
