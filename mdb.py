import sqlite3
import os
from loguru import logger
import util

DB_PATH = os.path.expandvars("%userprofile%\\appdata\\locallow\\Cygames\\umamusume\\master\\master.mdb")
SUPPORT_CARD_DICT = {}

class Connection():
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
    def __enter__(self):
        return self.conn, self.conn.cursor()
    def __exit__(self, type, value, traceback):
        self.conn.close()

def create_support_card_string(rarity, command_id, support_card_type, chara_id):
    return f"{util.SUPPORT_CARD_RARITY_DICT[rarity]} {util.SUPPORT_CARD_TYPE_DICT[(command_id, support_card_type)]} {util.get_character_name_dict()[chara_id]}"

def get_event_title(story_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT text FROM text_data WHERE category = 181 AND "index" = ? LIMIT 1""",
            (story_id,)
        )
        row = cursor.fetchone()
        if row is None:
            event_title = "NO EVENT TITLE"
            logger.warning(f"Event title not found for story_id: {story_id}")
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


def get_race_program_name_dict():
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT s.id, t.text FROM single_mode_program s INNER JOIN text_data t ON s.race_instance_id = t."index" AND t.category = 28"""
        )
        rows = cursor.fetchall()

    return {row[0]: row[1] for row in rows}

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
            """SELECT "index", text FROM text_data WHERE category = 14"""
        )
        rows = cursor.fetchall()

    return {row[0]: row[1] for row in rows}

def get_support_card_dict():
    global SUPPORT_CARD_DICT
    if not SUPPORT_CARD_DICT:
        with Connection() as (_, cursor):
            cursor.execute(
                """SELECT id, rarity, command_id, support_card_type, chara_id FROM support_card_data"""
            )
            rows = cursor.fetchall()
        SUPPORT_CARD_DICT = {row[0]: row[1:] for row in rows}
    return SUPPORT_CARD_DICT

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