# cogs/reaper/game.py
from datetime import datetime
from typing import Dict, Optional

class ReaperGame:
    def __init__(self, game_number: int, end: int, cooldown: int):
        self.game_number = game_number
        self.end = end
        self.cooldown = cooldown
        self.count = 0
        self.cooldowns: Dict[int, float] = {}
        self.message_id: Optional[int] = None

    def increment_count(self):
        """Increment the game counter by 1."""
        self.count += 1

    def can_reap(self, user_id: int) -> tuple[bool, Optional[int]]:
        """Check if a user can reap."""
        if user_id not in self.cooldowns:
            return True, None
            
        current_time = datetime.now().timestamp()
        time_diff = current_time - self.cooldowns[user_id]
        
        if time_diff < self.cooldown:
            return False, int(self.cooldown - time_diff)
        return True, None

    def reap(self, user_id: int) -> int:
        """Process a reap for a user."""
        reaped = self.count
        self.count = 0
        self.cooldowns[user_id] = datetime.now().timestamp()
        return reaped