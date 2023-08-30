import sqlite3
import os
from loguru import logger
import util
import constants
import gui

DB_PATH = os.path.expandvars("%userprofile%\\appdata\\locallow\\Cygames\\umamusume\\master\\master.mdb")

def update_mdb_cache():
    logger.info("Reloading cached dicts.")
    all_update_funcs = UPDATE_FUNCS + util.UPDATE_FUNCS
    for func in all_update_funcs:
        func(force=True)

CONNECTION_ERRORS = 5

class Connection():
    def __init__(self):
        try:
            self.conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        except sqlite3.OperationalError:
            util.show_error_box_no_report("Connection Error", "Could not connect to the game database.<br>Try restarting Uma Launcher after the game updates.<br>Uma Launcher will now close.")
            if gui.THREADER:
                gui.THREADER.stop()
    def __enter__(self):
        return self.conn, self.conn.cursor()
    def __exit__(self, type, value, traceback):
        self.conn.close()
        
        if type is not None:
            global CONNECTION_ERRORS
            CONNECTION_ERRORS += 1
            logger.error(f"Error: {type} {value}")
            logger.error(f"{traceback}")

            if CONNECTION_ERRORS > 5:
                util.show_error_box("Connection Error", "Could not connect to the game database.", custom_traceback=traceback)

            return True

def create_support_card_string(rarity, command_id, support_card_type, chara_id):
    return f"{constants.SUPPORT_CARD_RARITY_DICT[rarity]} {constants.SUPPORT_CARD_TYPE_DISPLAY_DICT[constants.SUPPORT_CARD_TYPE_DICT[(command_id, support_card_type)]]} {util.get_character_name_dict()[chara_id]}"

def get_columns(cursor):
    return [desc[0] for desc in cursor.description]

def rows_to_dict(rows, columns, keep_newline=False):
    return [{columns[i]: data if not isinstance(data, str) or keep_newline else data.replace("\\n", "") for i, data in enumerate(row)} for row in rows]

def get_event_title(story_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT text FROM text_data WHERE category = 181 AND "index" = ? LIMIT 1""",
            (story_id,)
        )
        row = cursor.fetchone()
        if row is None:
            event_title = "NO EVENT TITLE"
            logger.warning(f"Event title not found for story_id: {story_id}")  # TODO: Fix stories that aren't found.
        else:
            event_title = row[0]

    return event_title

def get_song_title(song_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT text FROM text_data WHERE category = 16 AND "index" = ? LIMIT 1""",
            (song_id,)
        )
        song_title = cursor.fetchone()[0]
    return song_title

def get_status_name(status_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT text FROM text_data WHERE category = 142 AND "index" = ? LIMIT 1""",
            (status_id,)
        )
        status_name = cursor.fetchone()[0]
    return status_name

def get_skill_name(skill_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT text FROM text_data WHERE category = 47 AND "index" = ? LIMIT 1""",
            (skill_id,)
        )
        skill_name = cursor.fetchone()[0]
    return skill_name

def get_skill_hint_name(group_id, rarity):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT td.text FROM skill_data sd INNER JOIN text_data td ON sd.id = td."index" AND td.category = 47 WHERE sd.group_id = ? AND sd.rarity = ? LIMIT 1""",
            (group_id, rarity)
        )
        skill_hint_name = cursor.fetchone()[0]
    return skill_hint_name

def get_race_program_name(program_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT t.text FROM single_mode_program s INNER JOIN text_data t ON s.race_instance_id = t."index" AND t.category = 28 WHERE s.id = ? LIMIT 1""",
            (program_id,)
        )
        program_name = cursor.fetchone()[0]
    return program_name

def get_outfit_name(card_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT text FROM text_data WHERE category = 14 AND "index" = ? LIMIT 1""",
            (card_id,)
        )
        outfit_name = cursor.fetchone()[0]
    return outfit_name

def get_support_card_string(support_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT rarity, command_id, support_card_type, chara_id FROM support_card_data WHERE id = ? LIMIT 1""",
            (support_id,)
        )
        row = cursor.fetchone()

        if row is None:
            logger.warning(f"Support card not found for id: {support_id}")
            return "SUPPORT CARD NOT FOUND"

    return create_support_card_string(*row)


def get_event_title_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT s.story_id, s.short_story_id, t.text FROM text_data t JOIN single_mode_story_data s ON t."index" = s.story_id WHERE category = 181"""
        )
        rows = cursor.fetchall()

    out = {}
    for row in rows:
        out[row[0]] = row[2]
        if row[1] != 0:
            out[row[1]] = row[2]
    return out

RACE_PROGRAM_NAME_DICT = {}
def get_race_program_name_dict(force=False):
    global RACE_PROGRAM_NAME_DICT
    if force or not RACE_PROGRAM_NAME_DICT:
        with Connection() as (_, cursor):
            cursor.execute(
                """SELECT s.id, t.text FROM single_mode_program s INNER JOIN text_data t ON s.race_instance_id = t."index" AND t.category = 28"""
            )
            rows = cursor.fetchall()
        RACE_PROGRAM_NAME_DICT.update({row[0]: row[1] for row in rows})
    return RACE_PROGRAM_NAME_DICT

def get_skill_name_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT sd.id, td.text FROM skill_data sd INNER JOIN text_data td ON sd.id = td."index" AND td.category = 47"""
        )
        rows = cursor.fetchall()

    return {row[0]: row[1] for row in rows}

def get_skill_hint_name_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT sd.group_id, sd.rarity, td.text FROM skill_data sd INNER JOIN text_data td ON sd.id = td."index" AND td.category = 47"""
        )
        rows = cursor.fetchall()

    return {(row[0], row[1]): row[2] for row in rows}

def get_status_name_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT "index", text FROM text_data WHERE category = 142"""
        )
        rows = cursor.fetchall()

    return {row[0]: row[1] for row in rows}

def get_outfit_name_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT "index", text FROM text_data WHERE category = 5"""
        )
        rows = cursor.fetchall()

    return {row[0]: row[1] for row in rows}

SUPPORT_CARD_DICT = {}
def get_support_card_dict(force=False):
    global SUPPORT_CARD_DICT
    if force or not SUPPORT_CARD_DICT:
        with Connection() as (_, cursor):
            cursor.execute(
                """SELECT id, rarity, command_id, support_card_type, chara_id FROM support_card_data"""
            )
            rows = cursor.fetchall()
        SUPPORT_CARD_DICT.update({row[0]: row[1:] for row in rows})
    return SUPPORT_CARD_DICT

def get_support_card_type(support_data):
    return constants.SUPPORT_CARD_TYPE_DICT[(support_data[1], support_data[2])]

def get_support_card_string_dict():
    support_card_dict = get_support_card_dict()
    return {id: create_support_card_string(*data) for id, data in support_card_dict.items()}

def get_chara_name_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT "index", text FROM text_data WHERE category = 170"""
        )
        rows = cursor.fetchall()

    return {row[0]: row[1] for row in rows}

def get_mant_item_string_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT "index", text FROM text_data WHERE category = 225"""
        )
        rows = cursor.fetchall()

    return {row[0]: row[1] for row in rows}

def get_gl_lesson_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT s.id, t.text, s.square_type FROM single_mode_live_square s JOIN text_data t ON t."index" = s.square_title_text_id AND t.category = 209"""
        )
        rows = cursor.fetchall()

    return {row[0]: (row[1], row[2]) for row in rows}

def get_group_card_effect_ids():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT id, effect_id FROM support_card_data WHERE support_card_type = 3"""
        )
        rows = cursor.fetchall()
    
    if not rows:
        return []

    return rows

def get_program_id_grade(program_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT r.grade FROM single_mode_program smp JOIN race_instance ri on smp.race_instance_id = ri.id JOIN race r on ri.race_id = r.id WHERE smp.id = ?;""",
            (program_id,)
        )
        row = cursor.fetchone()

    if not row:
        return None

    return row[0]

def get_program_id_data(program_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT * FROM single_mode_program WHERE id = ?;""",
            (program_id,)
        )
        rows = cursor.fetchall()
        columns = get_columns(cursor)
    
    if not rows:
        return None
    return rows_to_dict(rows, columns)[0]


def get_skill_id_dict():
    skill_id_dict = {}

    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT id, group_id, rarity, unique_skill_id_1 FROM skill_data ORDER BY group_rate DESC;"""
        )
        rows = cursor.fetchall()
    
    if not rows:
        return skill_id_dict
    
    for row in rows:
        true_id = row[0]
        # if row[3] != 0:
        #     true_id = row[3]
        
        skill_key = (row[1], row[2])
        if skill_key not in skill_id_dict:
            skill_id_dict[skill_key] = true_id
    
    return skill_id_dict


def get_card_inherent_skills(card_id, level=99):
    skills = []

    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT ass.skill_id FROM card_data cd JOIN available_skill_set ass ON cd.available_skill_set_id = ass.available_skill_set_id WHERE cd.id = ? AND ass.need_rank <= ?;""",
            (card_id, level)
        )
        rows = cursor.fetchall()
    
    if not rows:
        return skills
    
    for row in rows:
        skills.append(row[0])
    
    return skills

def sort_skills_by_display_order(skill_id_list):
    with Connection() as (_, cursor):
        cursor.execute(
            f"""SELECT id FROM skill_data WHERE id in ({','.join(['?'] * len(skill_id_list))}) ORDER BY disp_order ASC, id ASC;""",
            skill_id_list
        )
        rows = cursor.fetchall()
    
    if not rows:
        return None
    
    return [row[0] for row in rows]

def determine_skill_id_from_group_id(group_id, rarity, skills_id_list):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT id FROM skill_data WHERE group_id = ? AND rarity = ? AND group_rate > 0 ORDER BY group_rate ASC;""",
            (group_id, rarity)
        )
        rows = cursor.fetchall()
    
    if not rows:
        return None
    
    skill_id = None
    for row in rows:
        skill_id = row[0]
        if skill_id not in skills_id_list:
            break
        else:
            skills_id_list.remove(skill_id)
    
    return skill_id

UPDATE_FUNCS = [
    get_race_program_name_dict,
    get_support_card_dict,
]