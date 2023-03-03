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
