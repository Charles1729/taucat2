##################
# REAPERDB CLASS #
##################
# A class to store the Reaper Database.  Stored via SQL file.  There is
# only one database for all of Reaper.

from utils.db import Database
from typing import Optional, Dict, List, Tuple
import config

class ReaperDB:
    def __init__(self):
        self.db = Database(config.DATABASE_PATH)
        self._init_tables()
    
    def _init_tables(self):
        """
        Initializes the Reaper data table.  Ran once total.
        +--------------+-------------+---------------------+
        | user_id      | server_id   | reaped_seconds      |
        +--------------+-------------+---------------------+
        | ID of User   | ID of the   | Number of seconds   |
        | playing game | Server game | the User has reaped |
        |              | is played   | in the Server.      |
        +--------------+-------------+---------------------+
        
        Indexed (PRIMARY KEYed) via (user_id, server_id). 
        All Reaper data is stored in this table.
        
        Also initializes the game counters table - increments
        by one every time a game is played in a server.  QoL.
        """
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS reaper_scores (
                user_id INTEGER,
                server_id INTEGER,
                reaped_seconds INTEGER,
                PRIMARY KEY (user_id, server_id)
            )''')
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS game_counters (
                server_id INTEGER PRIMARY KEY,
                game_count INTEGER
            )''')

    def get_game_number(self, server_id: int) -> int:
        result = self.db.execute('SELECT game_count FROM game_counters WHERE server_id = ?', (server_id,))
        if not result:
            self.db.execute('INSERT INTO game_counters VALUES (?, 1)', (server_id,))
            return 1
        next_num = result[0][0] + 1
        self.db.execute('UPDATE game_counters SET game_count = ? WHERE server_id = ?', (next_num, server_id))
        return next_num

    def update_score(self, user_id: int, server_id: int, reaped: int) -> int:
        self.db.execute('''
            INSERT INTO reaper_scores (user_id, server_id, reaped_seconds)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, server_id)
            DO UPDATE SET reaped_seconds = reaped_seconds + ?
        ''', (user_id, server_id, reaped, reaped))
        
        result = self.db.execute(
            'SELECT reaped_seconds FROM reaper_scores WHERE user_id = ? AND server_id = ?',
            (user_id, server_id)
        )
        return result[0][0]

    def get_leaderboard(self, server_id: int) -> List[Tuple[int, int]]:
        """Get the top 10 scores for a server."""
        return self.db.execute('''
            SELECT user_id, reaped_seconds
            FROM reaper_scores
            WHERE server_id = ?
            ORDER BY reaped_seconds DESC
            LIMIT 10
        ''', (server_id,))

    def get_user_score(self, user_id: int, server_id: int) -> Optional[int]:
        """Get a specific user's score."""
        result = self.db.execute(
            'SELECT reaped_seconds FROM reaper_scores WHERE user_id = ? AND server_id = ?',
            (user_id, server_id)
        )
        return result[0][0] if result else None
    
    def end_game(self, server_id: int):
        """Delete all scores after game is over."""
        result = self.db.execute(
            'DELETE FROM reaper_scores WHERE server_id = ?',
            (server_id,))