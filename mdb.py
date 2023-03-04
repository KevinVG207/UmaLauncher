import sqlite3
import os
from loguru import logger

DB_PATH = os.path.expandvars("%userprofile%\\appdata\\locallow\\Cygames\\umamusume\\master\\master.mdb")

class Connection():
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
    def __enter__(self):
        return self.conn, self.conn.cursor()
    def __exit__(self, type, value, traceback):
        self.conn.close()

def get_event_title(story_id):
    with Connection() as (_, cursor):
        cursor.execute(
            """SELECT text FROM text_data t JOIN single_mode_story_data s ON t."index" = s.story_id WHERE category = 181 AND t."index" = ? OR s.short_story_id = ? LIMIT 1""",
            (story_id, story_id)
        )
        row = cursor.fetchone()
        if row is None:
            event_title = ""
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