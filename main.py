# main.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

class TaucatBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
    async def setup_hook(self):
        # Load all cogs
        await self.load_extension('cogs.reaper.cog')
        # Add more cogs as needed
        
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

def main():
    load_dotenv()
    bot = TaucatBot()
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()