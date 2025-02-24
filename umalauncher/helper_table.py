import copy
from loguru import logger
import mdb
import util
import constants
from helper_table_defaults import RowTypes


class TrainingPartner():
    def __init__(self, partner_id, starting_bond, chara_info):
        self.partner_id = partner_id
        self.starting_bond = starting_bond
        self.chara_info = chara_info
        self.chara_id = None

        if partner_id < 100:
            support_id = chara_info['support_card_array'][partner_id - 1]['support_card_id']
            support_data = mdb.get_support_card_dict()[support_id]
            chara_id = support_data[3]
            self.chara_id = chara_id
            self.img = f"https://gametora.com/images/umamusume/characters/icons/chr_icon_{chara_id}.png"
        elif partner_id > 1000:
            self.chara_id = partner_id
            self.img = f"https://gametora.com/images/umamusume/characters/icons/chr_icon_{partner_id}.png"
        else:
            try:
                chara_id = mdb.get_single_mode_unique_chara_dict()[chara_info['scenario_id']][partner_id]
                self.chara_id = chara_id
                self.img = f"https://gametora.com/images/umamusume/characters/icons/chr_icon_{chara_id}.png"
            except KeyError:
                self.img = "https://umapyoi.net/missing_chara.png"
                logger.error(f"Could not find unique chara_id for partner_id {partner_id} in scenario {chara_info['scenario_id']}")
        
        # Precalc-bonds
        bond, useful_bond, hint_bond, hint_useful_bond = self.calc_bonds()
        self.bond = bond
        self.useful_bond = useful_bond
        self.hint_bond = hint_bond
        self.hint_useful_bond = hint_useful_bond
    
    def add_effect_bonus_bond(self, bond):
        # Add 2 extra bond when charming is active and the partner is not Akikawa
        if self.partner_id <= 6 and 8 in self.chara_info.get('chara_effect_id_array', []):
            bond += 2

        # Add 2 extra bond when rising star is active and the partner is Akikawa
        elif self.partner_id == 102 and 9 in self.chara_info.get('chara_effect_id_array', []):
            bond += 2
        
        return bond
    
    def calc_bonds(self):
        bond = 0
        max_possible = min(100, 100 - self.starting_bond)
        # Akikawa is 102
        if self.partner_id < 1000:
            add = 7
            if self.partner_id <= 6:
                support_card_id = self.chara_info['support_card_array'][self.partner_id - 1]['support_card_id']
                support_card_data = mdb.get_support_card_dict()[support_card_id]
                support_card_type = constants.SUPPORT_CARD_TYPE_DICT[(support_card_data[1], support_card_data[2])]
                if support_card_type in ("group", "friend"):
                    add = 4
            
            bond += add

            bond = self.add_effect_bonus_bond(bond)

        bond = min(bond, max_possible)
        
        hint_bond = bond

        if self.partner_id <= 6:
            hint_bond += 5

        hint_bond = self.add_effect_bonus_bond(hint_bond)

        hint_bond = min(hint_bond, max_possible)

        hint_bond -= bond

        return max(bond, 0), max(self.calc_useful_bond(bond, self.starting_bond), 0), max(hint_bond, 0), max(self.calc_useful_bond(hint_bond, self.starting_bond + bond), 0)


    def calc_useful_bond(self, amount, starting_bond):
        usefulness_cutoff = 80
        
        # Ignore group and friend type cards except Satake Mei in Project L'Arc
        if self.partner_id <= 6:
            support_card_id = self.chara_info['support_card_array'][self.partner_id - 1]['support_card_id']

            if support_card_id in (10094, 30160) and self.chara_info['scenario_id'] in (6,):  # Only count Mei in Project L'Arc
                usefulness_cutoff = 60
            elif support_card_id in (10104, 30188) and self.chara_info['scenario_id'] in (7,):  # Only count Ryoka in UAF
                usefulness_cutoff = 60
            else:
                support_card_data = mdb.get_support_card_dict()[support_card_id]
                support_card_type = constants.SUPPORT_CARD_TYPE_DICT[(support_card_data[1], support_card_data[2])]
                if support_card_type in ("group", "friend"):
                    return 0

        cur_bond = amount + starting_bond
        effective_bond = 0

        if 6 < self.partner_id <= 1000:
            if self.partner_id in (102,) and not self.chara_info['scenario_id'] in (6,):  # Disable Akikawa usefulness in certain scenarios
                usefulness_cutoff = 60
            else:
                # Skip all non-Umas except Akikawa
                return 0

        new_bond = min(cur_bond, usefulness_cutoff)
        effective_bond = new_bond - starting_bond
        return max(effective_bond, 0)


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
        
        card_id = data['chara_info']['card_id']
        chara_id = int(str(card_id)[:4])
        
        turn = data['chara_info']['turn']
        scenario_id = data['chara_info']['scenario_id']
        energy = data['chara_info']['vital']
        max_energy = data['chara_info']['max_vital']
        fans = data['chara_info']['fans']
        skillpt = data['chara_info']['skill_point']

        arc_aptitude_points = 0
        arc_expectation_gauge = 0
        arc_supporter_points = 0

        command_info = {}

        all_commands = {}
        
        # Default commands
        for command in data['home_info']['command_info_array']:
            all_commands[command['command_id']] = copy.deepcopy(command)
        
        # Scenario specific commands
        # Obsolete, but works as reference for devs
        scenario_keys = [
            'venus_data_set',  # Grand Masters
            'live_data_set',  # Grand Live
            'free_data_set', # MANT
            'team_data_set',  # Aoharu
            'ura_data_set',  # URA
            'arc_data_set',  # Project L'Arc
            'sport_data_set',  # UAF Ready GO!,
            'cook_data_set',  # Great Food Festival
            'mecha_data_set',  # Run! Mecha Umamusume
        ]

        for key in data:
            if key.endswith("_data_set") and 'command_info_array' in data[key]:
                for command in data[key]['command_info_array']:
                    if 'params_inc_dec_info_array' in command:
                        # FIXME: make a proper fix for this. Maybe deepcopy the command if it's missing?
                        if command['command_id'] not in all_commands:
                            continue
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
        

        # Project L'Arc
        arc_charas = {}
        arc_beginning_or_overseas = False
        if 'arc_data_set' in data:
            for arc_chara in data['arc_data_set'].get('arc_rival_array', []):
                arc_charas[arc_chara['chara_id']] = arc_chara

            for command in data['arc_data_set'].get('command_info_array', []):
                if command['command_id'] in all_commands:
                    all_commands[command['command_id']]['add_global_exp'] = command['add_global_exp']

            arc_beginning_or_overseas = True
            # Make new command for Matches
            if 3 <= turn < 37 or 44 <= turn < 61:
                arc_beginning_or_overseas = False
                all_commands["ss_match"] = {
                    'command_id': "ss_match",
                    'params_inc_dec_info_array': data['arc_data_set'].get('selection_info', []).get('params_inc_dec_info_array', []) + \
                                                 data['arc_data_set'].get('selection_info', []).get('bonus_params_inc_dec_info_array', [])
                }

            for row in self.selected_preset:
                if isinstance(row, RowTypes.LARC_STAR_GAUGE_GAIN.value):
                    row.disabled = arc_beginning_or_overseas
                    break

        # Support Dict
        eval_dict = {
            eval_data['training_partner_id']: TrainingPartner(eval_data['training_partner_id'], eval_data['evaluation'], data['chara_info'])
            for eval_data in data['chara_info']['evaluation_info_array']
        }

        for command in all_commands.values():
            if command['command_id'] not in constants.COMMAND_ID_TO_KEY:
                continue
            level = command.get('level', 0)
            failure_rate = command.get('failure_rate', 0)
            gained_stats = {stat_type: 0 for stat_type in set(constants.COMMAND_ID_TO_KEY.values())}
            gained_skillpt = 0
            total_bond = 0
            useful_bond = 0
            gained_energy = 0
            rainbow_count = 0
            arc_aptitude_gain = 0

            for param in command.get('params_inc_dec_info_array', []):
                if param['target_type'] < 6:
                    gained_stats[constants.TARGET_TYPE_TO_KEY[param['target_type']]] += param['value']
                elif param['target_type'] == 30:
                    gained_skillpt += param['value']
                elif param['target_type'] == 10:
                    gained_energy += param['value']


            # Set up "training partners" for SS Match
            if command['command_id'] == 'ss_match':
                command['training_partner_array'] = []
                arc_eval_dict = {partner_data['chara_id']: partner_data['target_id'] for partner_data in data['arc_data_set']['evaluation_info_array']}
                
                for chara in data['arc_data_set']['selection_info']['selection_rival_info_array']:
                    partner_id = arc_eval_dict[chara['chara_id']]
                    command['training_partner_array'].append(partner_id)


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


            tip_gains_total = [0]
            tip_gains_useful = [0]
            bond_gains_total = [0]
            bond_gains_useful = [0]
            partner_count = 0
            useful_partner_count = 0
            for training_partner_id in command.get('training_partner_array', []):
                partner_count += 1

                # Detect if training_partner is rainbowing
                training_partner = eval_dict[training_partner_id]
                if training_partner_id <= 6:
                    # Partner is a support card
                    support_id = data['chara_info']['support_card_array'][training_partner_id - 1]['support_card_id']
                    support_data = mdb.get_support_card_dict()[support_id]
                    support_card_type = mdb.get_support_card_type(support_data)

                    # Don't count friend cards as useful except Mei Satake in Project L'Arc and Light Hello in Grand Live and Ryoka for UAF.
                    # This should probably be moved to a setting rather then beeing predefined for the user to customize
                    if support_card_type != 'friend' or support_id == 30160 and scenario_id in (6,) or support_id == 30052 and scenario_id in (3,) or support_id == 30188 and support_id in (7,):
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


                if training_partner_id in command.get('tips_event_partner_array', []):
                    tip_gains_total.append(training_partner.hint_bond)
                    tip_gains_useful.append(training_partner.hint_useful_bond)

                bond_gains_total.append(training_partner.bond)
                bond_gains_useful.append(training_partner.useful_bond)
            

            total_bond = sum(bond_gains_total)
            useful_bond = sum(bond_gains_useful)
            
            if not venus_blue_active:
                total_bond += max(tip_gains_total)
                useful_bond += max(tip_gains_useful)
            else:
                total_bond += sum(tip_gains_total)
                useful_bond += sum(tip_gains_useful)

            current_stats = data['chara_info'].get(constants.COMMAND_ID_TO_KEY[command['command_id']], 0)

            gl_tokens = {token_type: 0 for token_type in constants.GL_TOKEN_LIST}
            # Grand Live tokens
            if 'live_data_set' in data:
                for token_data in command['performance_inc_dec_info_array']:
                    gl_tokens[constants.GL_TOKEN_LIST[token_data['performance_type']-1]] += token_data['value']


            # L'Arc star gauge
            arc_gauge_gain = 0
            if 'arc_data_set' in data:
                # Aptitude points
                if 'add_global_exp' in command:
                    arc_aptitude_gain += command['add_global_exp']


                arc_eval_dict = {partner_data['target_id']: partner_data['chara_id'] for partner_data in data['arc_data_set']['evaluation_info_array']}

                for arc_chara_id in [arc_eval_dict[partner_id] for partner_id in command.get('training_partner_array', [])]:
                    if arc_chara_id in arc_charas:
                        arc_chara = arc_charas[arc_chara_id]
                        arc_gauge_gain += min(1 + rainbow_count, 3 - arc_chara['rival_boost'])  # TODO: Try to avoid doing this right after a match is done?

                # Override row data for SS Match
                if command['command_id'] == "ss_match":
                    # Partners
                    rival_dict = {rival['chara_id']: rival for rival in data['arc_data_set']['arc_rival_array']}
                    selection_list = data['arc_data_set']['selection_info']['selection_rival_info_array']
                    partner_count = len(selection_list)
                    useful_partner_count = partner_count

                    for rival in selection_list:
                        rival_data = rival_dict[rival['chara_id']]
                        effect_data = rival_data['selection_peff_array'][0]
                        effect_type = effect_data['effect_group_id']

                        if effect_type == 3:
                            # Energy recovery
                            gained_energy += 20

                        elif effect_type == 4:
                            # Max energy up & Energy recovery
                            gained_energy += 20

                        elif effect_type == 5:
                            # Motivation up & Energy recovery
                            gained_energy += 20

                        elif effect_type == 6:
                            # Star Gauge refill
                            arc_gauge_gain += 3
                        
                        elif effect_type == 7:
                            # Aptitude points
                            arc_aptitude_gain += 50

            gained_energy = min(gained_energy, max_energy - energy)


            # UAF Ready GO!
            uaf_sport_rank = {}
            uaf_sport_gain = {}
            uaf_current_active_effects = {}
            uaf_current_active_bonus = 0
            uaf_sport_competition = {}
            uaf_sport_rank_total = {2100: 0, 2200: 0, 2300: 0}
            uaf_required_rank_for_turn = {}
            uaf_current_required_rank = -1
            uaf_consultations_left = 0
            
            if 'sport_data_set' in data:
                sport_levels = data['sport_data_set'].get('training_array', [])
                uaf_sport_rank = {item['command_id']: item['sport_rank'] for item in sport_levels}
                uaf_sport_compeition_win = data['sport_data_set'].get('competition_result_array', [])
                
                uaf_active_effects = data['sport_data_set'].get('compe_effect_id_array', [])
                uaf_effects = mdb.get_uaf_training_effects()
                
                for effect_id in uaf_active_effects:
                    key = str(effect_id)[0]
                    value = uaf_effects.get(effect_id)

                    if value is not None:
                        uaf_current_active_effects[key] = value
                        uaf_current_active_bonus += value
                    
                group_counts = {'1': 0, '2': 0, '3': 0} # Janky hacky
                
                for competition in uaf_sport_compeition_win:
                    if competition.get("result_state") == 1:
                        for win_command_id in competition.get("win_command_id_array", []):
                            group = str(win_command_id)[1]
                            if group in group_counts:
                                group_counts[group] += 1
                
                uaf_sport_competition = f"{group_counts['1']}/{group_counts['2']}/{group_counts['3']}"

                uaf_consultations_left = len(data['sport_data_set'].get('item_id_array', []))
                
                uaf_required_rank_for_turn = mdb.get_uaf_required_rank_for_turn()
                uaf_required_rank_for_turn.sort(key=lambda x: x[0], reverse=1)
                
                for row in uaf_required_rank_for_turn:
                    if turn <= row[0]:
                        uaf_current_required_rank = row[1]
                
                # Calculate totals for each base
                for command_id, rank in uaf_sport_rank.items():
                    base = command_id - (command_id % 100)  # Get the base (2100, 2200, 2300, etc.)
                    uaf_sport_rank_total[base] += rank
                        
                command_info_array = data['sport_data_set']['command_info_array']
                
                # Extract and sort gain information
                gain_info_list = []
                for command_info in command_info_array:
                    for gain_info in command_info['gain_sport_rank_array']:
                        command_id = gain_info['command_id']
                        gain_rank = gain_info['gain_rank']
                        gain_info_list.append((command_id, gain_rank))
                        
                # Sort the list by the last digit of command_id and convert it back to dictionary
                gain_info_list.sort(key=lambda x: x[0] % 10)
                uaf_sport_gain = {command_id: gain_rank for command_id, gain_rank in gain_info_list}

            command_info[command['command_id']] = {
                'scenario_id': scenario_id,
                'current_stats': current_stats,
                'level': level,
                'partner_count': partner_count,
                'useful_partner_count': useful_partner_count,
                'failure_rate': failure_rate,
                'gained_stats': gained_stats,
                'gained_skillpt': gained_skillpt,
                'total_bond': total_bond,
                'useful_bond': useful_bond,
                'gained_energy': gained_energy,
                'rainbow_count': rainbow_count,
                'gm_fragment': spirit_id,
                'gm_fragment_double': spirit_boost,
                'gl_tokens': gl_tokens,
                'arc_gauge_gain': arc_gauge_gain,
                'arc_aptitude_gain': arc_aptitude_gain,
                'uaf_sport_gain': uaf_sport_gain,
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
                    util.show_warning_box(f"Could not get program data for program_id {race_data['program_id']}")
                    continue
                
                if program_data['base_program_id'] != 0:
                    program_data = mdb.get_program_id_data(program_data['base_program_id'])
                
                if not program_data:
                    util.show_warning_box(f"Could not get program data for program_id {race_data['program_id']}")
                    continue

                year = race_data['year'] - 1
                month = program_data['month'] - 1
                half = program_data['half'] - 1
                s_turn = 24 * year
                s_turn += month * 2
                s_turn += half
                s_turn += 1
                thumb_url = f"https://gametora.com/images/umamusume/race_banners/thum_race_rt_000_{str(program_data['race_instance_id'])[:4]}_00.png"

                scheduled_races.append({
                    "turn": s_turn,
                    "fans": program_data['need_fan_count'],
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

        # Project L'Arc Stats
        if 'arc_data_set' in data:
            arc_aptitude_points = data['arc_data_set']['arc_info']['global_exp']
            arc_expectation_gauge = data['arc_data_set']['arc_info']['approval_rate']
            arc_supporter_points = arc_charas[chara_id]['approval_point']
        
        # Great Food Festival
        gff_great_success = 0
        gff_success_point = 0
        gff_cooking_point = 0
        gff_tasting_thres = 0
        gff_tasting_great_thres = 0
        gff_vegetables = {}
        gff_field_point = [0, 0]
        if 'cook_data_set' in data:
            cook_data = data['cook_data_set']
            gff_cooking_point = cook_data['cook_info']['cooking_friends_power']
            gff_great_success = mdb.get_cooking_success_rate(gff_cooking_point)
            gff_success_point = cook_data['cook_info']['cooking_success_point']
            if gff_success_point >= 1500:
                gff_great_success = 100
            gff_tasting_thres, gff_tasting_great_thres = mdb.get_cooking_tasting_success_thresholds(data['chara_info']['turn'])
            gff_field_point[0] = cook_data['cook_info']['care_point']
            gff_field_point[1] = cook_data['care_point_gain_num']

            # Vegetables
            for veg_data in cook_data['material_info_array']:
                veg_dict = {
                    "id": veg_data['material_id'],
                    "count": veg_data['num'],
                    "max": 0,
                    "level": 0,
                    "harvest": 0,
                    "img": constants.GFF_VEG_ID_TO_IMG_ID[veg_data['material_id']],
                    "commands": {}
                }
                gff_vegetables[veg_data['material_id']] = veg_dict
            
            for fac_data in cook_data['facility_info_array']:
                fac_id = fac_data['facility_id']
                veg_dict = gff_vegetables[fac_id]
                veg_dict['level'] = fac_data['facility_level']
                veg_dict['max'] = mdb.get_cooking_vegetable_max_count(veg_dict['id'], veg_dict['level'])
            
            for harvest_data in cook_data['material_harvest_info_array']:
                veg_id = harvest_data['material_id']
                veg_dict = gff_vegetables[veg_id]
                veg_dict['harvest'] = harvest_data['harvest_num']
            
            for command_data in cook_data.get('command_material_care_info_array', []):
                if not command_data['command_type'] == 1:
                    continue
                
                command_id = command_data['command_id']
                cur_harvest_info = copy.deepcopy(command_data['material_harvest_info_array'])
                for harvest_info in cur_harvest_info:
                    veg_id = harvest_info['material_id']
                    veg_dict = gff_vegetables[veg_id]
                    harvest_info['harvest_num'] -= veg_dict['harvest']
                    harvest_info['img'] = veg_dict['img']
                command_info[constants.COMMAND_ID_TO_KEY[command_id]]['material_harvest_info_array'] = cur_harvest_info

        print(f"{gff_vegetables}")
            

        # Run! Mecha Umamusume
        if 'mecha_data_set' in data:
            mecha_data = data['mecha_data_set']
            for command_data in mecha_data.get('command_info_array', []):
                command_id = command_data['command_id']
                command_key = constants.COMMAND_ID_TO_KEY.get(command_id, None)
                if command_key and command_key in command_info and 'point_up_info_array' in command_data:
                    command_info[command_key]['point_up_info_array'] = command_data['point_up_info_array']


        main_info = {
            "turn": turn,
            "scenario_id": scenario_id,
            "energy": energy,
            "max_energy": max_energy,
            "fans": fans,
            "skillpt": skillpt,
            "scheduled_races": scheduled_races,
            "gm_fragments": gm_fragments,
            "gl_stats": gl_stats,
            "arc_aptitude_points": arc_aptitude_points,
            "arc_expectation_gauge": arc_expectation_gauge,
            "arc_supporter_points": arc_supporter_points,
            "uaf_sport_ranks": uaf_sport_rank,
            "uaf_sport_rank_total": uaf_sport_rank_total,
            "uaf_current_required_rank": uaf_current_required_rank,
            "uaf_current_active_effects": uaf_current_active_effects,
            "uaf_current_active_bonus": uaf_current_active_bonus,
            "uaf_sport_competition": uaf_sport_competition,
            "uaf_consultations_left": uaf_consultations_left,
            "gff_great_success": gff_great_success,
            "gff_success_point": gff_success_point,
            "gff_cooking_point": gff_cooking_point,
            "gff_tasting_thres": gff_tasting_thres,
            "gff_tasting_great_thres": gff_tasting_great_thres,
            "gff_vegetables": gff_vegetables,
            "gff_field_point": gff_field_point,
            "eval_dict": eval_dict,
            "all_commands": all_commands
        }

        # Update preset if needed.
        if self.carrotjuicer.threader.settings['training_helper_table_scenario_presets_enabled']:
            scenario_preset = self.carrotjuicer.threader.settings['training_helper_table_scenario_presets'].get(str(scenario_id), None)
            if scenario_preset and self.selected_preset.name != scenario_preset:
                self.selected_preset = self.carrotjuicer.threader.settings.get_preset_with_name(scenario_preset)
        else:
            general_preset = self.carrotjuicer.threader.settings['training_helper_table_preset']
            if self.selected_preset.name != general_preset:
                self.selected_preset = self.carrotjuicer.threader.settings.get_preset_with_name(general_preset)

        overlay_html = self.selected_preset.generate_overlay(main_info, command_info)

        return overlay_html
