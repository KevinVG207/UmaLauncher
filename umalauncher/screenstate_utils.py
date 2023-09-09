from loguru import logger
import screenstate as ss
import util
import constants
import mdb

def _make_default_training_state(data, handler) -> ss.ScreenState:
    new_state = ss.ScreenState(handler)

    new_state.location = ss.Location.TRAINING

    new_state.main = f"Training - {util.turn_to_string(data['chara_info']['turn'])}"

    outfit_id = data['chara_info']['card_id']
    chara_id = int(str(outfit_id)[:-2])
    scenario_id = data['chara_info']['scenario_id']
    scenario_name = constants.SCENARIO_DICT.get(scenario_id, None)
    if not scenario_name:
        logger.error(f"Scenario ID not found in scenario dict: {scenario_id}")
        scenario_name = "You are now breathing manually."
    new_state.set_chara(chara_id, outfit_id=outfit_id, small_text=scenario_name)
    return new_state

def make_training_state(data, handler) -> ss.ScreenState:
    new_state = _make_default_training_state(data, handler)
    new_state.sub = f"{data['chara_info']['speed']} {data['chara_info']['stamina']} {data['chara_info']['power']} {data['chara_info']['guts']} {data['chara_info']['wiz']} | {data['chara_info']['skill_point']}"
    return new_state

def make_training_race_state(data, handler) -> ss.ScreenState:
    new_state = _make_default_training_state(data, handler)
    new_state.sub = f"In race: {util.get_race_name_dict()[data['race_start_info']['program_id']]}"
    return new_state

def make_concert_state(music_id, handler) -> ss.ScreenState:
    new_state = ss.ScreenState(handler)
    new_state.location = ss.Location.THEATER
    new_state.set_music(music_id)
    return new_state

def get_league_of_heroes_substate(league_score):
    return f"Rank: {util.heroes_score_to_league_string(league_score)} ({league_score}pt)"

def make_league_of_heroes_state(handler, team_name, league_score) -> ss.ScreenState:
    new_state = ss.ScreenState(handler)
    new_state.location = ss.Location.LEAGUE_OF_HEROES
    new_state.main = f"League of Heroes - {team_name}"
    new_state.sub = get_league_of_heroes_substate(league_score)
    return new_state

def make_scouting_state(handler: ss.ScreenStateHandler, team_score, outfit_id) -> ss.ScreenState:
    new_state = ss.ScreenState(handler)
    new_state.location = ss.Location.SCOUTING_EVENT
    new_state.main = f"Team Building - {team_score} pt."
    new_state.sub = f"Rank: {util.scouting_score_to_rank_string(team_score)}"

    chara_id = str(outfit_id)[:-2]

    new_state.set_chara(chara_id, outfit_id=int(outfit_id), small_text="Team Leader")

    return new_state

def make_claw_machine_state(packet_data, handler: ss.ScreenStateHandler) -> ss.ScreenState:
    new_state = ss.ScreenState(handler)
    new_state.location = ss.Location.CLAW_MACHINE
    new_state.main = "Playing the Claw Machine"
    new_state.large_image = "claw_machine"

    unique_count = 0
    # total_count = 0
    for plushie in packet_data['collected_plushies']:
        unique_count += 1
        # total_count += plushie['count']
    
    total_unique_count = mdb.get_total_minigame_plushies()

    new_state.sub = f"Collected: {unique_count} / {total_unique_count}"
    return new_state
