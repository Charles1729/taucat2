# cogs/reaper/database.py
from utils.db import Database
from typing import Optional, Dict, List, Tuple
import config

class ReaperDB:
    def __init__(self):
        self.db = Database(config.DATABASE_PATH)
        self._init_tables()
    
    def _init_tables(self):
        """Initialize the required tables for the Reaper game."""
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS reaper_scores (
                user_id INTEGER,
                server_id INTEGER,
                reaped_seconds INTEGER,
                PRIMARY KEY (user_id, server_id)
            )
        ''')
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS game_counters (
                server_id INTEGER PRIMARY KEY,
                game_count INTEGER
            )
        ''')

    def get_game_number(self, server_id: int) -> int:
        """Get the next game number for a server."""
        result = self.db.execute(
            'SELECT game_count FROM game_counters WHERE server_id = ?',
            (server_id,)
        )
        
        if not result:
            self.db.execute(
                'INSERT INTO game_counters VALUES (?, 1)',
                (server_id,)
            )
            return 1
            
        current_count = result[0][0]
        next_count = current_count + 1
        
        self.db.execute(
            'UPDATE game_counters SET game_count = ? WHERE server_id = ?',
            (next_count, server_id)
        )
        
        return next_count

    def update_score(self, user_id: int, server_id: int, reaped: int) -> int:
        """Update a user's score and return their new total."""
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