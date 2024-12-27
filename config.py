# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_PATH = 'data/taucat.db'

# Reaper game configuration
REAPER_CHANNEL = 'tau-reaper'
ADMIN_ROLE = 'taucater'