import copy
from loguru import logger
import mdb
import util
import constants


class TrainingPartner():
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
        if self.carrotjuicer.last_helper_data and self.carrotjuicer.browser and self.carrotjuicer.browser.alive():
            self.carrotjuicer.update_helper_table(self.carrotjuicer.last_helper_data)


    def create_helper_elements(self, data, last_data) -> str:
        """Creates the helper elements for the given response packet.
        """
        # Transfer data from last data if it does not exist in the current data
        if last_data:
            if 'reserved_race_array' not in data and 'reserved_race_array' in last_data:
                data['reserved_race_array'] = last_data['reserved_race_array']

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

        # Venus specific
        if 'venus_data_set' in data:
            for spirit_data in data['venus_data_set']['venus_chara_command_info_array']:
                if spirit_data['command_id'] in all_commands:
                    all_commands[spirit_data['command_id']]['spirit_data'] = spirit_data

        # Grand Live specific
        if 'live_data_set' in data:
            for command in data['live_data_set']['command_info_array']:
                all_commands[command['command_id']]['performance_inc_dec_info_array'] = command['performance_inc_dec_info_array']

        for command in all_commands.values():
            if command['command_id'] not in constants.COMMAND_ID_TO_KEY:
                continue

            eval_dict = {
                eval_data['training_partner_id']: TrainingPartner(eval_data['training_partner_id'], eval_data['evaluation'])
                for eval_data in data['chara_info']['evaluation_info_array']
            }
            level = command['level']
            failure_rate = command['failure_rate']
            gained_stats = {stat_type: 0 for stat_type in set(constants.COMMAND_ID_TO_KEY.values())}
            skillpt = 0
            total_bond = 0
            useful_bond = 0
            energy = 0
            rainbow_count = 0

            for param in command['params_inc_dec_info_array']:
                if param['target_type'] < 6:
                    gained_stats[constants.TARGET_TYPE_TO_KEY[param['target_type']]] += param['value']
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
                if 'spirit_data' in command:
                    spirit_id = command['spirit_data']['spirit_id']
                    spirit_boost = command['spirit_data']['is_boost']
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
                    support_card_type = constants.SUPPORT_CARD_TYPE_DICT[(support_card_data[1], support_card_data[2])]
                    if support_card_type in ("group", "friend"):
                        return 0

                cur_bond = eval_dict[partner_id].starting_bond
                effective_bond = 0

                usefulness_cutoff = 80
                if partner_id == 102:
                    usefulness_cutoff = 60

                if cur_bond < usefulness_cutoff:
                    new_bond = cur_bond + amount
                    new_bond = min(new_bond, 80)
                    effective_bond = new_bond - cur_bond
                return effective_bond


            tip_gains_total = [0]
            tip_gains_useful = [0]
            partner_count = 0
            useful_partner_count = 0
            for training_partner_id in command['training_partner_array']:
                partner_count += 1

                # Detect if training_partner is rainbowing
                training_partner = eval_dict[training_partner_id]
                if training_partner_id <= 6:
                    # Partner is a support card
                    support_id = data['chara_info']['support_card_array'][training_partner_id - 1]['support_card_id']
                    support_data = mdb.get_support_card_dict()[support_id]
                    support_card_type = mdb.get_support_card_type(support_data)

                    if support_card_type != 'friend':
                        useful_partner_count += 1

                    if support_card_type not in ("group", "friend") and training_partner.starting_bond >= 80 and command['command_id'] in constants.SUPPORT_TYPE_TO_COMMAND_IDS[support_card_type]:
                        rainbow_count += 1
                    elif support_card_type == "group" and util.get_group_support_id_to_passion_zone_effect_id_dict()[support_id] in data['chara_info']['chara_effect_id_array']:
                        rainbow_count += 1
                    elif support_card_type != 'friend' and 'venus_data_set' in data and \
                            len(data['venus_data_set']['venus_spirit_active_effect_info_array']) > 0 and \
                                data['venus_data_set']['venus_spirit_active_effect_info_array'][0]['chara_id'] == 9042:
                        rainbow_count += 1
                elif training_partner_id > 1000:  # TODO: Maybe 1000 < training_partner_id < 9000
                    useful_partner_count += 1

                # Cap bond at 100
                new_bond = min(training_partner.starting_bond + training_partner.training_bond, 100)
                true_training_gain = new_bond - training_partner.starting_bond
                total_bond += true_training_gain
                useful_bond += calc_bond_gain(training_partner.partner_id, true_training_gain)
                training_partner.starting_bond = new_bond

                # Cap bond at 100 again
                new_bond = min(training_partner.starting_bond + training_partner.tip_bond, 100)
                true_tip_gain = new_bond - training_partner.starting_bond
                tip_gains_total.append(true_tip_gain)

                new_tip_total = training_partner.starting_bond + true_tip_gain
                if new_tip_total < 80:
                    tip_gains_useful.append(true_tip_gain)
                else:
                    tip_gains_useful.append(max(0, 80 - training_partner.starting_bond))

                training_partner.starting_bond = new_bond
            
            if not venus_blue_active:
                total_bond += max(tip_gains_total)
                useful_bond += max(tip_gains_useful)
            else:
                total_bond += sum(tip_gains_total)
                useful_bond += sum(tip_gains_useful)

            current_stats = data['chara_info'][constants.COMMAND_ID_TO_KEY[command['command_id']]]

            gl_tokens = {token_type: 0 for token_type in constants.GL_TOKEN_LIST}
            # Grand Live tokens
            if 'live_data_set' in data:
                for token_data in command['performance_inc_dec_info_array']:
                    gl_tokens[constants.GL_TOKEN_LIST[token_data['performance_type']-1]] += token_data['value']

            command_info[command['command_id']] = {
                'scenario_id': data['chara_info']['scenario_id'],
                'current_stats': current_stats,
                'level': level,
                'partner_count': partner_count,
                'useful_partner_count': useful_partner_count,
                'failure_rate': failure_rate,
                'gained_stats': gained_stats,
                'gained_skillpt': skillpt,
                'total_bond': total_bond,
                'useful_bond': useful_bond,
                'gained_energy': energy,
                'rainbow_count': rainbow_count,
                'gm_fragment': spirit_id,
                'gm_fragment_double': spirit_boost,
                'gl_tokens': gl_tokens,
            }

        # Simplify everything down to a dict with only the keys we care about.
        # No distinction between normal and summer training.
        command_info = {
            constants.COMMAND_ID_TO_KEY[command_id]: command_info[command_id]
            for command_id in command_info
            if command_id in constants.COMMAND_ID_TO_KEY
        }


        # Process scheduled races
        scheduled_races = []
        if 'reserved_race_array' in data:
            for race_data in data['reserved_race_array'][0]['race_array']:
                # TODO: Maybe cache the mdb data for all race programs?
                program_data = mdb.get_program_id_data(race_data['program_id'])
                if not program_data:
                    logger.warning(f"Could not get program data for program_id {race_data['program_id']}")
                    continue
                year = race_data['year'] - 1
                month = program_data['month'] - 1
                half = program_data['half'] - 1
                turn = 24 * year
                turn += month * 2
                turn += half
                turn += 1
                thumb_url = f"https://gametora.com/images/umamusume/race_banners/thum_race_rt_000_{str(program_data['race_instance_id'])[:4]}_00.png"

                scheduled_races.append({
                    "turn": turn,
                    "thumb_url": thumb_url
                })
            
            scheduled_races.sort(key=lambda x: x['turn'])

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
            "turn": data['chara_info']['turn'],
            "scenario_id": data['chara_info']['scenario_id'],
            "energy": data['chara_info']['vital'],
            "max_energy": data['chara_info']['max_vital'],
            "scheduled_races": scheduled_races,
            "gm_fragments": gm_fragments,
            "gl_stats": gl_stats,
        }

        overlay_html = self.selected_preset.generate_overlay(main_info, command_info)

        return overlay_html
