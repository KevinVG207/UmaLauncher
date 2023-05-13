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