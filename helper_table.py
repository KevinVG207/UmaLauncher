from loguru import logger
import mdb
import util
import gui
import helper_table_defaults as htd

COMMAND_ID_TO_KEY = {
    101: "speed",
    105: "stamina",
    102: "power",
    103: "guts",
    106: "wiz",
    601: "speed",
    602: "stamina",
    603: "power",
    604: "guts",
    605: "wiz"
}

class HelperTable():
    carrotjuicer = None
    preset = None
    last_game_state = None

    def __init__(self, carrotjuicer):
        self.carrotjuicer = carrotjuicer
        self.preset = htd.DefaultPreset(htd.row_types)

    def create_helper_table(self, data) -> str:
        """Creates a helper table for the given game state.
        """

        if not 'home_info' in data:
            return None

        eval_dict = {eval_data['training_partner_id']: eval_data['evaluation'] for eval_data in data['chara_info']['evaluation_info_array']}

        game_state = {}

        all_commands = {}
        
        # Default commands
        for command in data['home_info']['command_info_array']:
            all_commands[command['command_id']] = command
        
        # Scenario specific commands
        scenario_keys = [
            'venus_data_set',  # Grand Masters
            'live_data_set',  # Grand Live
            'free_data_set', # MANT
            'team_data_set',  # Aoharu
            'ura_data_set'  # URA
        ]
        for key in scenario_keys:
            if key in data and 'command_info_array' in data[key]:
                for command in data[key]['command_info_array']:
                    if 'params_inc_dec_info_array' in command:
                        all_commands[command['command_id']]['params_inc_dec_info_array'] += command['params_inc_dec_info_array']

        for command in all_commands.values():
            if command['command_id'] not in COMMAND_ID_TO_KEY:
                continue

            level = command['level']
            failure_rate = command['failure_rate']
            stats = 0
            skillpt = 0
            bond = 0
            energy = 0

            for param in command['params_inc_dec_info_array']:
                if param['target_type'] < 6:
                    stats += param['value']
                elif param['target_type'] == 30:
                    skillpt += param['value']
                elif param['target_type'] == 10:
                    energy += param['value']
            
            
            def calc_bond_gain(partner_id, amount):
                if not partner_id in eval_dict:
                    logger.error(f"Training partner ID not found in eval dict: {partner_id}")
                    return 0
                
                # Ignore group and friend type cards
                if partner_id <= 6:
                    support_card_id = data['chara_info']['support_card_array'][partner_id - 1]['support_card_id']
                    support_card_data = mdb.get_support_card_dict()[support_card_id]
                    support_card_type = util.SUPPORT_CARD_TYPE_DICT[(support_card_data[1], support_card_data[2])]
                    if support_card_type in ("Group", "Friend"):
                        return 0

                cur_bond = eval_dict[partner_id]
                effective_bond = 0

                usefulness_cutoff = 81
                if partner_id == 102:
                    usefulness_cutoff = 61

                if cur_bond < usefulness_cutoff:
                    new_bond = cur_bond + amount
                    new_bond = min(new_bond, 80)
                    effective_bond = new_bond - cur_bond
                return effective_bond

            for training_partner_id in command['training_partner_array']:
                # Akikawa is 102
                if training_partner_id <= 6 or training_partner_id == 102:
                    initial_gain = 7
                    # Add 2 extra bond when charming is active and the partner is not Akikawa
                    if training_partner_id <= 6 and 8 in data['chara_info'].get('chara_effect_id_array', []):
                        initial_gain += 2

                    # Add 2 extra bond when rising star is active and the partner is Akikawa
                    elif training_partner_id == 102 and 9 in data['chara_info'].get('chara_effect_id_array', []):
                        initial_gain += 2

                    bond += calc_bond_gain(training_partner_id, initial_gain)

            # For bond, first check if blue venus effect is active.
            venus_blue_active = False
            if 'venus_data_set' in data and len(data['venus_data_set']['venus_spirit_active_effect_info_array']) > 0:
                if data['venus_data_set']['venus_spirit_active_effect_info_array'][0]['chara_id'] == 9041:
                    venus_blue_active = True

            bond_gains = [0]
            for tips_partner_id in command['tips_event_partner_array']:
                if tips_partner_id <= 6:
                    bond_gains.append(calc_bond_gain(tips_partner_id, 5))
            if not venus_blue_active:
                bond += max(bond_gains)
            else:
                bond += sum(bond_gains)

            current_stats = data['chara_info'][COMMAND_ID_TO_KEY[command['command_id']]]

            game_state[command['command_id']] = {
                'current_stats': current_stats,
                'level': level,
                'failure_rate': failure_rate,
                'gained_stats': stats,
                'gained_skillpt': skillpt,
                'useful_bond': bond,
                'gained_energy': energy
            }

        # Simplify everything down to a dict with only the keys we care about.
        # No distinction between normal and summer training.
        game_state = {
            COMMAND_ID_TO_KEY[command_id]: game_state[command_id]
            for command_id in game_state
            if command_id in COMMAND_ID_TO_KEY
        }

        self.last_game_state = game_state

        table = self.preset.generate_table(game_state)

        return table

    def show_preset_menu(self):
        """Shows a menu to select a preset.
        """

        app = gui.UmaApp()
        app.run()