import copy
from loguru import logger
import mdb
import util


class BondMember():
    def __init__(self, partner_id, starting_bond):
        self.partner_id = partner_id
        self.starting_bond = starting_bond
        self.training_bond = 0
        self.tip_bond = 0


class HelperTable():
    carrotjuicer = None
    selected_preset = None
    preset_dict = None

    def __init__(self, carrotjuicer):
        self.carrotjuicer = carrotjuicer
        self.preset_dict = {}
        self.selected_preset = None
        self.preset_dict, self.selected_preset = self.carrotjuicer.threader.settings.get_helper_table_data()

    def update_presets(self, preset_dict, selected_preset):
        self.preset_dict = preset_dict
        self.selected_preset = selected_preset
        if self.carrotjuicer.last_helper_data and self.carrotjuicer.browser:
            self.carrotjuicer.check_browser()
            self.carrotjuicer.update_helper_table(self.carrotjuicer.last_helper_data)


    def create_helper_elements(self, data) -> str:
        """Creates the helper elements for the given response packet.
        """

        if not 'home_info' in data:
            return None

        command_info = {}

        all_commands = {}
        
        # Default commands
        for command in data['home_info']['command_info_array']:
            all_commands[command['command_id']] = copy.deepcopy(command)
        
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
            if command['command_id'] not in util.COMMAND_ID_TO_KEY:
                continue

            eval_dict = {
                eval_data['training_partner_id']: BondMember(eval_data['training_partner_id'], eval_data['evaluation'])
                for eval_data in data['chara_info']['evaluation_info_array']
            }
            level = command['level']
            failure_rate = command['failure_rate']
            gained_stats = {stat_type: 0 for stat_type in set(util.COMMAND_ID_TO_KEY.values())}
            skillpt = 0
            total_bond = 0
            useful_bond = 0
            energy = 0

            for param in command['params_inc_dec_info_array']:
                if param['target_type'] < 6:
                    gained_stats[util.TARGET_TYPE_TO_KEY[param['target_type']]] += param['value']
                elif param['target_type'] == 30:
                    skillpt += param['value']
                elif param['target_type'] == 10:
                    energy += param['value']

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

                    eval_dict[training_partner_id].training_bond += initial_gain

            for tips_partner_id in command['tips_event_partner_array']:
                if tips_partner_id <= 6:
                    eval_dict[tips_partner_id].tip_bond += 5

            # For bond, first check if blue venus effect is active.
            spirit_id = 0
            spirit_boost = 0
            venus_blue_active = False
            if 'venus_data_set' in data:
                for spirit_data in data['venus_data_set']['venus_chara_command_info_array']:
                    if spirit_data['command_id'] == command['command_id']:
                        spirit_id = spirit_data['spirit_id']
                        spirit_boost = spirit_data['is_boost']
                        break

                if len(data['venus_data_set']['venus_spirit_active_effect_info_array']) > 0 and data['venus_data_set']['venus_spirit_active_effect_info_array'][0]['chara_id'] == 9041:
                    venus_blue_active = True


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

                cur_bond = eval_dict[partner_id].starting_bond
                effective_bond = 0

                usefulness_cutoff = 81
                if partner_id == 102:
                    usefulness_cutoff = 61

                if cur_bond < usefulness_cutoff:
                    new_bond = cur_bond + amount
                    new_bond = min(new_bond, 80)
                    effective_bond = new_bond - cur_bond
                return effective_bond


            tip_gains_total = []
            tip_gains_useful = []
            for bond_member in eval_dict.values():
                # Cap bond at 100
                new_bond = min(bond_member.starting_bond + bond_member.training_bond, 100)
                true_training_gain = new_bond - bond_member.starting_bond
                total_bond += true_training_gain
                useful_bond += calc_bond_gain(bond_member.partner_id, true_training_gain)
                bond_member.starting_bond = new_bond

                # Cap bond at 100 again
                new_bond = min(bond_member.starting_bond + bond_member.tip_bond, 100)
                true_tip_gain = new_bond - bond_member.starting_bond
                tip_gains_total.append(true_tip_gain)

                new_tip_total = bond_member.starting_bond + true_tip_gain
                if new_tip_total < 81:
                    tip_gains_useful.append(true_tip_gain)
                else:
                    tip_gains_useful.append(max(0, 81 - bond_member.starting_bond))

                bond_member.starting_bond = new_bond
            
            if not venus_blue_active:
                total_bond += max(tip_gains_total)
                useful_bond += max(tip_gains_useful)
            else:
                total_bond += sum(tip_gains_total)
                useful_bond += sum(tip_gains_useful)

            current_stats = data['chara_info'][util.COMMAND_ID_TO_KEY[command['command_id']]]

            command_info[command['command_id']] = {
                'scenario_id': data['chara_info']['scenario_id'],
                'current_stats': current_stats,
                'level': level,
                'failure_rate': failure_rate,
                'gained_stats': gained_stats,
                'gained_skillpt': skillpt,
                'total_bond': total_bond,
                'useful_bond': useful_bond,
                'gained_energy': energy,
                'gm_fragment': spirit_id,
                'gm_fragment_double': spirit_boost,
            }

        # Simplify everything down to a dict with only the keys we care about.
        # No distinction between normal and summer training.
        command_info = {
            util.COMMAND_ID_TO_KEY[command_id]: command_info[command_id]
            for command_id in command_info
            if command_id in util.COMMAND_ID_TO_KEY
        }

        # Grand Masters Fragments
        gm_fragments = [0] * 8
        if 'venus_data_set' in data:
            fragments = data['venus_data_set']['spirit_info_array']
            for fragment in fragments:
                if fragment['spirit_num'] <= 8:
                    gm_fragments[fragment['spirit_num'] - 1] = fragment['spirit_id']
        
        # Grand Live Stats
        gl_stats = {}
        if 'live_data_set' in data:
            gl_stats = data['live_data_set']['live_performance_info']


        main_info = {
            "scenario_id": data['chara_info']['scenario_id'],
            "energy": data['chara_info']['vital'],
            "max_energy": data['chara_info']['max_vital'],
            "gm_fragments": gm_fragments,
            "gl_stats": gl_stats,
        }

        overlay_html = self.selected_preset.generate_overlay(main_info, command_info)

        return overlay_html
