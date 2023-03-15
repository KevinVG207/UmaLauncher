from enum import Enum
import os
# Tell it to create a new training
# add() function which takes a training data packet
# plot() function

# What to track
# Each turn
## Stats
## Which skills
# Each event
## What was gained


# Different types of event to track
# Training
# Training Event/Rest/Date
# Buying skills
# Race

# Example response = packet_in.json

def join_with_sep(parts, sep=','):
    return sep.join(str(part) if part is not None else '' for part in parts)

def nparse(val, _type):
    # Parse a value to a type, but return None if it's an empty string.
    if val == '':
        return None
    return _type(val)


class TrainingTracker():
    training_log_folder = None
    training_id = None
    action_list = None

    def __init__(self, training_log_folder: str, training_id: str):
        self.action_list = []

        self.training_log_folder = training_log_folder
        self.training_id = training_id

        # Check if this training id already exists
        if os.path.exists(self.get_csv_path()):
            # Load the existing training
            with open(self.get_csv_path(), 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    direction = PacketDirection[parts[1]]
                    if direction == PacketDirection.IN:
                        self.action_list.append(BaseResponse.from_csv_parts(parts))
                    else:
                        self.action_list.append(BaseRequest.from_csv_parts(parts))

    def get_csv_path(self):
        return str(os.path.join(self.training_log_folder, self.training_id)) + ".csv"

    def add_response(self, packet_data):
        # Write the previous action to file.
        # This is because user might close the game and there will be a duplicate action.
        self.write_to_csv()
        self.action_list.append(BaseResponse.from_packet(packet_data, PacketDirection.IN))
        return

    def add_request(self, packet_data):
        pass

    def write_to_csv(self):
        with open(self.get_csv_path(), 'w', encoding='utf-8') as f:
            f.write(join_with_sep(self.action_list, '\n'))


class MainStats():
    speed = None
    stamina = None
    power = None
    guts = None
    wisdom = None
    skill_pts = None
    energy = None
    motivation = None
    fans = None

    def __init__(self, chara_info: dict):
        if not chara_info:
            return
        self.speed = chara_info.get('speed')
        self.stamina = chara_info.get('stamina')
        self.power = chara_info.get('power')
        self.guts = chara_info.get('guts')
        self.wisdom = chara_info.get('wiz')
        self.skill_pts = chara_info.get('skill_point')
        self.energy = chara_info.get('vital')
        self.motivation = chara_info.get('motivation')
        self.fans = chara_info.get('fans')

    def to_csv_string(self):
        out_string_parts = [
            self.speed,
            self.stamina,
            self.power,
            self.guts,
            self.wisdom,
            self.skill_pts,
            self.energy,
            self.motivation,
            self.fans
        ]
        out_string = join_with_sep(out_string_parts, ',')
        return out_string

    @classmethod
    def from_csv_parts(cls, parts: list):
        return cls({
            'speed': nparse(parts[0], int),
            'stamina': nparse(parts[1], int),
            'power': nparse(parts[2], int),
            'guts': nparse(parts[3], int),
            'wiz': nparse(parts[4], int),
            'skill_point': nparse(parts[5], int),
            'vital': nparse(parts[6], int),
            'motivation': nparse(parts[7], int),
            'fans': nparse(parts[8], int)
        })


class StatIncrement():
    target_type = None
    value = None
    def __init__(self, stat_increment: dict):
        if not stat_increment:
            return
        self.target_type = stat_increment.get('target_type')
        self.value = stat_increment.get('value')

    def to_csv_string(self):
        out_string_parts = [
            self.target_type,
            self.value
        ]
        out_string = join_with_sep(out_string_parts, ':')
        return out_string
    
    @classmethod
    def from_csv_string(cls, csv_string: str):
        parts = csv_string.split(':')
        return {
            'target_type': nparse(parts[0], int),
            'value': nparse(parts[1], int)
        }


class Command():
    cmd_type = None
    cmd_id = None
    enabled = None
    failure_rate = None
    level = None
    stat_increments = None
    def __init__(self, command_info: dict):
        if not command_info:
            return
        self.cmd_type = command_info.get('command_type')
        self.cmd_id = command_info.get('command_id')
        self.enabled = command_info.get('is_enable')
        self.failure_rate = command_info.get('failure_rate')
        self.level = command_info.get('level')
        self.stat_increments = []
        for stat_increment in command_info.get('params_inc_dec_info_array'):
            self.stat_increments.append(StatIncrement(stat_increment))

    def to_csv_string(self):
        out_string_parts = [
            self.cmd_type,
            self.cmd_id,
            self.enabled,
            self.failure_rate,
            self.level
        ]
        stat_increment_parts = []
        for stat_increment in self.stat_increments:
            stat_increment_parts.append(stat_increment.to_csv_string())
        out_string_parts.append("|".join(stat_increment_parts))
        out_string = join_with_sep(out_string_parts, ',')
        return out_string

    @classmethod
    def from_csv_parts(cls, parts: list):
        return {
            'command_type': nparse(parts[0], int),
            'command_id': nparse(parts[1], int),
            'is_enable': nparse(parts[2], int),
            'failure_rate': nparse(parts[3], int),
            'level': nparse(parts[4], int),
            'params_inc_dec_info_array': [StatIncrement.from_csv_string(part) for part in parts[5].split('|')]
        }


class TrainingCommands():
    training_speed = Command(None)
    training_stamina = Command(None)
    training_power = Command(None)
    training_guts = Command(None)
    training_wisdom = Command(None)
    def __init__(self, command_info_array: dict):
        if not command_info_array:
            return
        current_commands = {
            (command.get('command_type'), command.get('command_id')): command
            for command in command_info_array
            if command.get('command_type', None) is not None
        }
        if current_commands:
            self.training_speed =   Command(current_commands[(1, 101)])
            self.training_stamina = Command(current_commands[(1, 105)])
            self.training_power =   Command(current_commands[(1, 102)])
            self.training_guts =    Command(current_commands[(1, 103)])
            self.training_wisdom =  Command(current_commands[(1, 106)])


    def to_csv_string(self):
        out_string_parts = [
            self.training_speed.to_csv_string(),
            self.training_stamina.to_csv_string(),
            self.training_power.to_csv_string(),
            self.training_guts.to_csv_string(),
            self.training_wisdom.to_csv_string()
        ]
        out_string = join_with_sep(out_string_parts, ',')
        return out_string


    @classmethod
    def from_csv_parts(cls, parts: list):
        return cls([
            Command.from_csv_parts(parts[i:i+6])
            for i in range(0, len(parts), 6)
        ])

class ActionType(Enum):
    NOTHING = 0
    TRAINING = 1
    TRAINING_EVENT = 2
    BUY_SKILL = 3
    RACE = 4
    REST = 5
    OUTING = 6

class PacketDirection(Enum):
    IN = 0
    OUT = 1

class BaseResponse():
    turn = 0
    direction = PacketDirection.IN
    action_type = ActionType.NOTHING
    stats = MainStats(None)
    commands = TrainingCommands(None)

    def __init__(self, action_data):
        self.turn = action_data.get('turn')
        self.action_type = action_data.get('action_type')
        self.stats = action_data.get('stats')
        self.commands = action_data.get('commands')

    @classmethod
    def from_packet(cls, packet_data, direction: PacketDirection):
        # if not packet_data:
        #     return
        stats = MainStats(packet_data['chara_info'])
        home_info = packet_data.get('home_info')
        if home_info:
            commands = TrainingCommands(home_info.get('command_info_array', None))
        else:
            commands = TrainingCommands(None)

        action_data = {
            'turn': packet_data['chara_info']['turn'],
            'action_type': ActionType.NOTHING,  # Change this
            'stats': stats,
            'commands': commands
        }
        return cls(action_data)

    def to_csv_string(self):
        # Function that turns everything into a csv string
        out_string_parts = [
            self.turn,
            self.direction.name,
            self.action_type.name,
            self.stats.to_csv_string(),
            self.commands.to_csv_string()
        ]
        out_string = ','.join(str(part) if part else '' for part in out_string_parts)
        return out_string

    @classmethod
    def from_csv_parts(cls, parts: list):
        return cls({
            'turn': int(parts[0]),
            # 'direction': PacketDirection[parts[1]],
            'action_type': ActionType[parts[2]],
            'stats': MainStats.from_csv_parts(parts[3:12]),
            'commands': TrainingCommands.from_csv_parts(parts[12:])
        })

    def __str__(self):
        return self.to_csv_string()

class TrainingEventEvent(BaseResponse):
    pass

class BuySkillEvent(BaseResponse):
    pass

class RaceEvent(BaseResponse):
    pass

class Skill():
    skill_id = None
    level = None
    def __init__(self, skill_data):
        if not skill_data:
            return
        self.skill_id = skill_data.get('skill_id')
        self.level = skill_data.get('level')
    
    def to_csv_string(self):
        out_string_parts = [
            self.skill_id,
            self.level
        ]
        out_string = join_with_sep(out_string_parts, ':')
        return out_string


class BoughtSkills():
    skills_list = []
    def __init__(self, skills_data):
        if not skills_data:
            return
        self.skills_list = [Skill(skill) for skill in skills_data]

    def __sizeof__(self) -> int:
        return len(self.skills_list)

    def to_csv_string(self):
        out_string_parts = [
            skill.to_csv_string()
            for skill in self.skills_list
        ]
        out_string = join_with_sep(out_string_parts, '|')
        return out_string


class BaseRequest():
    current_turn = None

    # Training Event
    event_id = None
    chara_id = None
    choice_number = None

    # Training
    command_type = None
    command_id = None
    command_group_id = None
    select_id = None

    # Buying skills
    bought_skills = None

    # Racing
    program_id = None

    direction = PacketDirection.OUT
    action_type = ActionType.NOTHING

    def __init__(self, request_data, bought_skills: BoughtSkills):
        self.current_turn = request_data.get('current_turn')
        self.event_id = request_data.get('event_id')
        self.chara_id = request_data.get('chara_id')
        self.choice_number = request_data.get('choice_number')
        self.command_type = request_data.get('command_type')
        self.command_id = request_data.get('command_id')
        self.command_group_id = request_data.get('command_group_id')
        self.select_id = request_data.get('select_id')
        self.program_id = request_data.get('program_id')
        self.bought_skills = bought_skills

        if self.command_type == 1:
            self.action_type = ActionType.TRAINING
        elif self.command_type == 3:
            self.action_type = ActionType.OUTING
        elif self.command_type == 7:
            self.action_type = ActionType.REST
        elif self.event_id is not None:
            self.action_type = ActionType.TRAINING_EVENT
        elif self.program_id is not None:
            self.action_type = ActionType.RACE
        elif len(self.bought_skills) > 0:
            self.action_type = ActionType.BUY_SKILL

    @classmethod
    def from_packet(cls, request_data):
        if 'gain_skill_info_array' in request_data:
            bought_skills = BoughtSkills(request_data['gain_skill_info_array'])
        bought_skills = request_data.get()
        return cls(request_data, bought_skills)

    def to_csv_string(self):
        out_string_parts = [
            self.current_turn,
            self.direction.name,
            self.action_type.name,
            self.event_id,
            self.chara_id,
            self.choice_number,
            self.command_type,
            self.command_id,
            self.command_group_id,
            self.select_id,
            self.program_id,
            self.bought_skills.to_csv_string()
        ]
        out_string = ','.join(str(part) if part else '' for part in out_string_parts)
        return out_string

    @classmethod
    def from_csv_parts(cls, parts):
        pass


# import packet_in
# import packet_out
# response_packet = packet_in.packet
# request_packet = packet_out.packet
# tracker = TrainingTracker("test.csv")
# tracker.add_response(response_packet)
# tracker.write_to_csv()

# print('a')


# New version:
# Don't do anything during the run, just save the data.
# Load each packet json, add to list and pickle the list.
# Then, after the run, do the analysis.
# Then, save the results to a csv file.
# Then, delete the pickle file.
