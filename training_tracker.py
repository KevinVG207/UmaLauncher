import os
import json
import gzip
import re
import time
import threading
import traceback
import win32gui
import win32con
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
from external import race_data_parser


class TrainingTracker():
    training_log_folder = None
    training_id = None

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
        self.write_packet(packet)


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


    def get_training_path(self):
        return str(os.path.join(self.training_log_folder, self.training_id))


    def get_sav_path(self):
        return self.get_training_path() + ".gz"


    def get_csv_path(self):
        return self.get_training_path() + ".csv"


    def write_packet(self, packet: dict):
        # Convert to json string and save with gzip
        # Append to gzip if file exists
        is_first = not os.path.exists(self.get_sav_path())
        if packet is not None:
            with gzip.open(self.get_sav_path(), 'ab') as f:
                if not is_first:
                    f.write(','.encode('utf-8'))
                f.write(json.dumps(packet, ensure_ascii=False).encode('utf-8'))


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
        # app.run(TrainingAnalyzerGui(app))
        app.set_training_tracker(self)
        app.to_csv()
        app.close()

    def to_csv_list(self):
        app = TrainingAnalyzer(self)
        csv_list = app.to_csv_list()
        app.close()
        return csv_list


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
    """Represents the type of action that was taken in the training scenario.
    Negative values are actions that may be ignored."""
    AfterRace2 = -2
    BeforeRace = -1
    Unknown = 0
    Start = 1
    End = 2
    Training = 3
    Event = 4
    Race = 5
    SkillHint = 6
    BuySkill = 7
    Rest = 8
    Outing = 9
    Infirmary = 10
    GoddessWisdom = 11
    BuyItem = 12
    UseItem = 13
    Lesson = 14
    AfterRace = 15
    Continue = 16
    AoharuRaces = 17

class CommandType(Enum):
    Speed = 101
    Stamina = 105
    Power = 102
    Guts = 103
    Wisdom = 106
    SummerSpeed = 601
    SummerStamina = 602
    SummerPower = 603
    SummerGuts = 604
    SummerWisdom = 605


@dataclass
class TrainingAction():
    """Represents a single training action.
    d = delta.
    """
    # TODO: Aptitudes
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
    value: int = 0
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
    add_status: set = field(default_factory=set)
    remove_status: set = field(default_factory=set)


class TrainingAnalyzer():
    training_tracker = None
    packets = None
    last_turn = 0
    scenario_id = None
    card_id = None
    chara_id = None
    support_cards = None
    last_program_id = None
    last_failure_rates = {}
    last_mant_shop_items_dict = {}
    next_action_type = None
    gm_effect_active = False
    action_list = []
    chara_names_dict = util.get_character_name_dict()
    event_title_dict = mdb.get_event_title_dict()
    race_program_name_dict = mdb.get_race_program_name_dict()
    skill_name_dict = mdb.get_skill_name_dict()
    skill_hint_name_dict = mdb.get_skill_hint_name_dict()
    status_name_dict = mdb.get_status_name_dict()
    outfit_name_dict = util.get_outfit_name_dict()
    support_card_string_dict = mdb.get_support_card_string_dict()
    mant_item_string_dict = mdb.get_mant_item_string_dict()
    gl_lesson_dict = mdb.get_gl_lesson_dict()

    def __init__(self):
        pass

    def set_training_tracker(self, training_tracker):
        self.training_tracker = training_tracker
        self.packets = None
        self.last_turn = 0
        self.scenario_id = None
        self.card_id = None
        self.chara_id = None
        self.support_cards = None
        self.last_program_id = None
        self.last_failure_rates = {}
        self.last_mant_shop_items_dict = {}
        self.next_action_type = None
        self.gm_effect_active = False
        self.action_list = []
        self.packets = self.training_tracker.load_packets()

    def to_csv_list(self):
        self.action_list = []

        # Grab req/resp pairs
        prev_resp = None
        # for i in range(0, len(self.packets), 2):
        packet_index = 0
        while packet_index < len(self.packets) - 1:
            req = self.packets[packet_index]
            resp = self.packets[packet_index+1]

            # Check if response really is a response
            while resp['_direction'] != 1:
                packet_index += 1
                resp = self.packets[packet_index+1]
            packet_index += 2

            if 'chara_info' in resp:
                chara_info = resp['chara_info']

                if self.last_turn == 0:
                    # First turn, set all static values.
                    self.scenario_id = chara_info['scenario_id']
                    self.card_id = chara_info['card_id']
                    self.chara_id = int(str(self.card_id)[:4])
                    self.support_cards = chara_info['support_card_array']

                # Create base action
                action = TrainingAction(
                    turn = req['current_turn'] if 'current_turn' in req else chara_info['turn'],
                    speed = chara_info['speed'],
                    stamina = chara_info['stamina'],
                    power = chara_info['power'],
                    guts = chara_info['guts'],
                    wisdom = chara_info['wiz'],
                    skill_pt = chara_info['skill_point'],
                    energy = chara_info['vital'],
                    motivation = chara_info['motivation'],
                    fans = chara_info['fans'],
                    skill = {tuple(item.values()) for item in chara_info['skill_array']},
                    skillhint = {tuple(item.values()) for item in chara_info['skill_tips_array']},
                    status = set(chara_info['chara_effect_id_array'])
                )
            
            elif 'race_scenario' in resp and resp['race_scenario']:
                # Race packet
                this_horse_data = resp['race_start_info']['race_horse_data'][0]
                action = TrainingAction(
                    turn = req['current_turn'],
                    speed = this_horse_data['speed'],
                    stamina = this_horse_data['stamina'],
                    power = this_horse_data['pow'],
                    guts = this_horse_data['guts'],
                    wisdom = this_horse_data['wiz'],
                    skill_pt = self.action_list[-1].skill_pt,
                    energy = self.action_list[-1].energy,
                    motivation = this_horse_data['motivation'],
                    fans = this_horse_data['fan_count'],
                    skill = {tuple(item.values()) for item in this_horse_data['skill_array']},
                    skillhint = self.action_list[-1].skillhint,
                    status = self.action_list[-1].status
                )

            else:
                # Unknown packet
                logger.error(f'Unknown response packet type at index {packet_index}: {resp}')
                continue

            # Determine if turn changed
            if action.turn > self.last_turn:
                self.last_turn = action.turn
                # Reset some values
                self.gm_effect_active = False

            # Calculate deltas
            if self.action_list:
                prev_action = self.action_list[-1]
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
                action.add_status = action.status - prev_action.status
                action.remove_status = prev_action.status - action.status


            # Determine action type
            self.determine_action_type(req, resp, action, prev_resp)

            # Add to list
            self.action_list.append(action)

            if 'home_info' in resp:
                self.last_failure_rates = {command['command_id']: command['failure_rate'] for command in resp['home_info']['command_info_array']}

            prev_resp = resp

        # Write to CSV
        scenario_str = util.SCENARIO_DICT.get(self.scenario_id, 'Unknown')
        chara_str = f"{self.chara_names_dict.get(self.chara_id, 'Unknown')} - {self.outfit_name_dict[self.card_id]}"
        support_1_str = f"{self.support_cards[0]['support_card_id']} - {self.support_card_string_dict[self.support_cards[0]['support_card_id']]}"
        support_2_str = f"{self.support_cards[1]['support_card_id']} - {self.support_card_string_dict[self.support_cards[1]['support_card_id']]}"
        support_3_str = f"{self.support_cards[2]['support_card_id']} - {self.support_card_string_dict[self.support_cards[2]['support_card_id']]}"
        support_4_str = f"{self.support_cards[3]['support_card_id']} - {self.support_card_string_dict[self.support_cards[3]['support_card_id']]}"
        support_5_str = f"{self.support_cards[4]['support_card_id']} - {self.support_card_string_dict[self.support_cards[4]['support_card_id']]}"
        support_6_str = f"{self.support_cards[5]['support_card_id']} - {self.support_card_string_dict[self.support_cards[5]['support_card_id']]}"

        headers = [
                ("Scenario", lambda _: scenario_str),
                ("Chara", lambda _: chara_str),
                ("Support 1", lambda _: support_1_str),
                ("Support 2", lambda _: support_2_str),
                ("Support 3", lambda _: support_3_str),
                ("Support 4", lambda _: support_4_str),
                ("Support 5", lambda _: support_5_str),
                ("Support 6", lambda _: support_6_str),
                ("Turn", lambda x: x.turn),
                ("Action", lambda x: x.action_type.name),
                ("Text", lambda x: x.text),
                ("Value", lambda x: x.value),
                ("SPD", lambda x: x.speed),
                ("STA", lambda x: x.stamina),
                ("POW", lambda x: x.power),
                ("GUT", lambda x: x.guts),
                ("INT", lambda x: x.wisdom),
                ("SKLPT", lambda x: x.skill_pt),
                ("ERG", lambda x: x.energy),
                ("MOT", lambda x: util.MOTIVATION_DICT.get(x.motivation, "Unknown")),
                ("FAN", lambda x: x.fans),

                ("ΔSPD", lambda x: x.dspeed),
                ("ΔSTA", lambda x: x.dstamina),
                ("ΔPOW", lambda x: x.dpower),
                ("ΔGUT", lambda x: x.dguts),
                ("ΔINT", lambda x: x.dwisdom),
                ("ΔSKLPT", lambda x: x.dskill_pt),
                ("ΔERG", lambda x: x.denergy),
                ("ΔMOT", lambda x: x.dmotivation),
                ("ΔFAN", lambda x: x.dfans),
                ("Skills Added", lambda x: "|".join([self.skill_name_dict[skill[0]] + f" LVL{skill[1]}" for skill in x.add_skill])),
                ("Skills Removed", lambda x: "|".join([self.skill_name_dict[skill[0]] + f" LVL{skill[1]}" for skill in x.remove_skill])),
                ("Skill Hints Added", lambda x: "|".join([self.skill_hint_name_dict[(skillhint[0], skillhint[1])] + f" LVL{skillhint[2]}" for skillhint in x.add_skillhint])),
                ("Statuses Added", lambda x: "|".join([self.status_name_dict[status] for status in x.add_status])),
                ("Statuses Removed", lambda x: "|".join([self.status_name_dict[status] for status in x.remove_status])),
            ]

        # Create CSV
        out_rows = []

        header_row = ",".join([header[0] for header in headers])
        out_rows.append(header_row)

        def remove_zero(value):
            if value in (0, '0'):
                return ""
            return value

        for action in self.action_list:
            # Ignore certain actions
            if action.action_type.value < 0:
                continue
            if action.action_type == ActionType.Unknown:
                # Skip action if it does not gain or lose any stats or skills/statuses etc.
                if not any([action.dspeed,
                            action.dstamina,
                            action.dpower,
                            action.dguts,
                            action.dwisdom,
                            action.dskill_pt,
                            action.denergy,
                            action.dmotivation,
                            action.dfans,
                            action.add_skill,
                            action.remove_skill,
                            action.add_skillhint,
                            action.add_status,
                            action.remove_status]):
                    continue
            row = ",".join([str(remove_zero(header[1](action))) for header in headers])
            out_rows.append(row)

        return out_rows


    def to_csv(self):
        t1 = time.perf_counter()
        with open(self.training_tracker.get_csv_path(), 'w', encoding='utf-8') as csvfile:
            csvfile.write("\n".join(self.to_csv_list()))
        t2 = time.perf_counter()
        logger.debug(f"CSV generation took {t2-t1:0.4f} seconds")


    def determine_action_type(self, req: dict, resp: dict, action: TrainingAction, prev_resp: dict):
        # Request specific:

        # Start of run
        if 'start_chara' in req and req['start_chara']:
            action.action_type = ActionType.Start
            action.text = util.create_gametora_helper_url(self.card_id, self.scenario_id, [item['support_card_id'] for item in self.support_cards])
            return
        
        # Continue after failed race
        if 'continue_type' in req and req['continue_type']:
            action.action_type = ActionType.Continue
            action.value = req['continue_type']
            return

        # Save MANT shop items.
        if self.scenario_id == 4 and 'free_data_set' in resp:
            if resp['free_data_set'].get('pick_up_item_info_array'):
                self.last_mant_shop_items_dict = {item_dict['shop_item_id']: item_dict['item_id']
                                                  for item_dict in resp['free_data_set']['pick_up_item_info_array']}

        # Event requested by client
        if 'event_id' in req and req['event_id']:
            if not prev_resp:
                action.action_type = ActionType.Unknown
                action.text = "Unknown due to missing previous packet. Could be an event or skill hint."
                return

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
            action.text = self.event_title_dict[story_id]
            action.value = req['choice_number']
            return

        if 'command_type' in req and req['command_type']:
            # Training
            if req['command_type'] == 1:
                action.action_type = ActionType.Training
                action.text = CommandType(req['command_id']).name
                if req['command_id'] not in self.last_failure_rates:
                    action.value = -1
                else:
                    action.value = self.last_failure_rates[req['command_id']]
                return

            # Resting
            if req['command_type'] == 7:  # and req['command_id'] == 701:
                action.action_type = ActionType.Rest
                return

            # Outing
            if req['command_type'] == 3:
                action.action_type = ActionType.Outing
                select_id = req['select_id']
                chara_id = self.chara_id if select_id == 0 else select_id
                action.text = self.chara_names_dict[chara_id]
                return

            # Infirmary
            if req['command_type'] == 8:
                action.action_type = ActionType.Infirmary
                return

        if 'gain_skill_info_array' in req and req['gain_skill_info_array']:
            # Skill(s) bought
            action.action_type = ActionType.BuySkill
            return

        # Response-specific:

        if 'race_reward_info' in resp and resp['race_reward_info']:
            # Race Completed
            action.action_type = ActionType.AfterRace
            action.text = self.race_program_name_dict[self.last_program_id]
            action.value = resp['race_reward_info']['result_rank']  # Saving the finishing position here for now.
            # self.next_action_type = ActionType.AfterRace2
            return
        
        if 'race_scenario' in resp and resp['race_scenario']:
            # Race Packet
            return self.make_race_action(action, resp)


        # Grand Masters specific
        if self.scenario_id == 5:
            if not 'venus_data_set' in resp or resp['venus_data_set'] is None:
                return
            
            venus = resp['venus_data_set']

            # Goddess Wisdom
            if len(venus['venus_spirit_active_effect_info_array']) > 0 and not self.gm_effect_active:
                self.gm_effect_active = True
                action.action_type = ActionType.GoddessWisdom
                goddess_chara_id = venus['venus_spirit_active_effect_info_array'][0]['chara_id']
                action.text = self.chara_names_dict[goddess_chara_id]
                action.value = {chara_dict['chara_id']: chara_dict['venus_level'] for chara_dict in venus['venus_chara_info_array']}[goddess_chara_id]
                return

            # Venus Race Packet
            if 'race_scenario' in venus and venus['race_scenario']:
                return self.make_race_action(action, venus)

            # Venus race results
            if 'race_reward_info' in venus and venus['race_reward_info'] is not None:
                action.action_type = ActionType.AfterRace
                action.text = self.race_program_name_dict[self.last_program_id]
                return
        
        # MANT specific
        if self.scenario_id == 4:
            # Buying MANT items.
            if 'exchange_item_info_array' in req:
                action.action_type = ActionType.BuyItem
                action.text = '|'.join(self.mant_item_string_dict[self.last_mant_shop_items_dict[item['shop_item_id']]] for item in req['exchange_item_info_array'])
                return

            if 'use_item_info_array' in req:
                action.action_type = ActionType.UseItem
                action.text = '|'.join(self.mant_item_string_dict[item['item_id']] for item in req['use_item_info_array'])
                return
        
        # Grand Live specific
        if self.scenario_id == 3:
            if 'square_id' in req:
                action.action_type = ActionType.Lesson
                gl_lesson = self.gl_lesson_dict[req['square_id']]
                action.text = gl_lesson[0]
                action.value = gl_lesson[1]
                return
            
        # Aoharu specific
        if self.scenario_id == 2:
            if 'team_race_set_id' in req:
                action.action_type = ActionType.AoharuRaces
                results = [0, 0, 0]
                for race in resp['team_data_set']['race_result_array']:
                    results[race['win_type']-1] += 1
                action.text = f"{results[0]} WIN - {results[1]} LOSS - {results[2]} DRAW"
                return

        return
    

    def make_race_action(self, action: TrainingAction, race_dict: dict):
        race_data = race_dict['race_start_info']
        race_scenario = race_data_parser.parse(race_dict['race_scenario'])
        action.action_type = ActionType.Race
        action.text = self.race_program_name_dict[race_data['program_id']]
        frame_order = race_data['race_horse_data'][0]['frame_order']
        action.value = race_scenario.horse_result[frame_order-1].finish_order + 1  # Saving the finishing position here for now.
        self.last_program_id = race_data['program_id']
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


class TrainingCombiner:
    training_paths = None
    output_file_path = None
    result = None

    def __init__(self, training_paths, output_file_path, result: list):
        self.training_paths = training_paths
        self.output_file_path = output_file_path
        self.result = result

    def combine(self):
        csvs = []
        training_analyzer = TrainingAnalyzer()
        for training_path in self.training_paths:
            try:
                training_path_only, training_name = os.path.split(training_path)
                training_name, _ = os.path.splitext(training_name)
                training_analyzer.set_training_tracker(TrainingTracker(training_name, training_path_only))
                csvs.append(training_analyzer.to_csv_list())
            except Exception:
                logger.error(traceback.format_exc())
                util.show_error_box("Error", f"Error while generating CSV for {training_path}")
                self.result.append(False)
                logger.debug("Error while generating CSV for %s", training_path)
                return

        with open(self.output_file_path, 'w', encoding='utf-8') as csv_file:
            first = True
            for i, rows in enumerate(csvs):
                if not first:
                    csv_file.write("\n")
                header = True
                for j, row in enumerate(rows):
                    if len(self.training_paths) > 1:
                        if header:
                            header = False
                            if not first:
                                rows[j] = ''
                                continue
                            first = False
                            rows[j] = "Run," + row
                        else:
                            rows[j] = f"{i + 1}," + row
                csv_file.write("\n".join(row for row in rows if row))
        self.result.append(True)
        logger.debug("Finished generating CSV for %s", self.output_file_path)
        return


def combine_trainings(training_paths, output_file_path):
    result = []
    
    combiner = TrainingCombiner(training_paths, output_file_path, result)
    combiner_thread = threading.Thread(target=combiner.combine)
    logger.debug("Starting thread to generate CSV")
    combiner_thread.start()

    logger.debug("Starting GUI")
    app = gui.UmaApp()
    logger.debug("Running popup")
    app.run(gui.UmaBorderlessPopup(app, "Creating CSV", "Creating CSV...", combiner_thread, result))
    logger.debug("Finished popup")

    return result[0]


def training_csv_dialog(training_paths=None):
    if training_paths is None:
        try:
            training_paths, _, _ = win32gui.GetOpenFileNameW(
                InitialDir="training_logs",
                Title="Select training log(s)",
                Flags=win32con.OFN_ALLOWMULTISELECT | win32con.OFN_FILEMUSTEXIST | win32con.OFN_EXPLORER,
                DefExt="gz",
                Filter="Training logs (*.gz)\0*.gz\0\0"
            )

            training_paths = training_paths.split("\0")
            if len(training_paths) > 1:
                dir_path = training_paths[0]
                training_paths = [os.path.join(dir_path, training_path) for training_path in training_paths[1:]]

        except util.pywinerror:
            util.show_error_box("Error", "No file(s) selected.")
            return

    # Check if all files end with .gz
    # If not, show error message
    for training_path in training_paths:
        if not training_path.endswith(".gz"):
            util.show_error_box("Error", "All chosen files must be .gz (gzip) files.")
            return

    try:
        output_file_path, _, _ = win32gui.GetSaveFileNameW(
            InitialDir="training_logs",
            Title="Select output file",
            Flags=win32con.OFN_EXPLORER | win32con.OFN_OVERWRITEPROMPT | win32con.OFN_PATHMUSTEXIST,
            File="training",
            DefExt="csv",
            Filter="CSV (*.csv)\0*.csv\0\0"
        )

    except util.pywinerror:
        util.show_error_box("Error", "No output file given.")
        return

    if not output_file_path.endswith(".csv"):
        output_file_path += ".csv"

    if not combine_trainings(training_paths, output_file_path):
        return

    util.show_info_box("Success", "CSV successfully created.")
    return


def main():
    # TrainingTracker('2023_03_17_03_58_38').analyze()
    names = [
        r".\training_logs\2023_03_21_05_26_30.gz",
    ]
    combine_trainings(names, "training_logs/combined.csv")
    print("a")

if __name__ == "__main__":
    main()
