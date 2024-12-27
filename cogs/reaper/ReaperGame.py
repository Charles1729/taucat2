####################
# REAPERGAME CLASS #
####################
# A class to store information about individual Reaper games inindividual
# servers.  Only 1 per server allowed.

from datetime import datetime
from typing import Dict, Optional

class ReaperGame:
    def __init__(self, game_number: int, end: int, cooldown: int):
        """
        game_number: The Reaper game number.  Increments by 1 every single
                     time a game is played in a server.  Starts at 1.
        end:         The number of seconds a player needs to reap to win.
        cooldown:    The number of seconds between reaps.
        last_reap:   The POSIX timestamp of the last reap.
        cooldowns:   An internal Dict to keep track of users and their
                     last reap time, as a POSIX timestamp
        message_id:  It needs to send a message.
        """
        
        self.game_number = game_number
        self.end = end
        self.cooldown = cooldown
        self.last_reap = datetime.now().timestamp()
        self.cooldowns: Dict[int, float] = {}
        self.message_id: Optional[int] = None

    def can_reap(self, user_id: int) -> tuple[bool, Optional[int]]:
        if user_id not in self.cooldowns:
            return True, None

        time_diff = datetime.now().timestamp() - self.cooldowns[user_id]
        if time_diff < self.cooldown:
            return False, int(self.cooldown - time_diff)
        return True, None

    def reap(self, user_id: int) -> int:
        cur_time = datetime.now().timestamp()
        reaped = int(cur_time - self.last_reap)
        self.last_reap = cur_time
        self.cooldowns[user_id] = cur_time
        return reaped
    
    def get_count(self) -> int:
        cur_time = datetime.now().timestamp()
        return int(cur_time - self.last_reap)