# cogs/reaper/cog.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import config
from .database import ReaperDB
from .game import ReaperGame
from typing import Dict

class ReaperCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = ReaperDB()
        self.active_games: Dict[int, ReaperGame] = {}
        self.count_updater.start()

    def cog_unload(self):
        self.count_updater.cancel()

    @tasks.loop(seconds=1)
    async def count_updater(self):
        """Update all active game counters."""
        for game in self.active_games.values():
            game.increment_count()

    @count_updater.before_loop
    async def before_count_updater(self):
        """Wait until the bot is ready before starting the counter."""
        await self.bot.wait_until_ready()

    reaper_group = app_commands.Group(name="reaper", description="Reaper game commands")

    @reaper_group.command(name="start", description="Start a new Reaper game")
    @app_commands.describe(
        cooldown="Seconds between reaps",
        end="Target seconds to win"
    )
    async def reaper_start(self, interaction: discord.Interaction, cooldown: int, end: int):
        """Start a new Reaper game in the server."""
        if interaction.channel.name != config.REAPER_CHANNEL:
            await interaction.response.send_message(
                f"This command can only be used in the #{config.REAPER_CHANNEL} channel. Please create one!",
                ephemeral=True
            )
            return

        if not any(role.name == config.ADMIN_ROLE for role in interaction.user.roles):
            await interaction.response.send_message(
                f"You need the '{config.ADMIN_ROLE}' role to start a game!",
                ephemeral=True
            )
            return

        if interaction.guild_id in self.active_games:
            await interaction.response.send_message(
                "A game is already in progress!",
                ephemeral=True
            )
            return

        game_number = self.db.get_game_number(interaction.guild_id)
        game = ReaperGame(game_number, end, cooldown)
        self.active_games[interaction.guild_id] = game

        message = await interaction.channel.send(
            f"Game {game_number} in {interaction.guild.name} has begun! "
            f"Reap {end} seconds to win, with {cooldown} seconds between successive reaps."
        )
        await message.pin()
        game.message_id = message.id
        
        await interaction.response.send_message("Game started successfully!", ephemeral=True)

    @reaper_group.command(name="reap", description="Reap the current counter")
    async def reaper_reap(self, interaction: discord.Interaction):
        """Reap the current counter in an active game."""
        if interaction.channel.name != config.REAPER_CHANNEL:
            await interaction.response.send_message(
                f"This command can only be used in the #{config.REAPER_CHANNEL} channel!",
                ephemeral=True
            )
            return

        if interaction.guild_id not in self.active_games:
            await interaction.response.send_message(
                "No game is currently running!",
                ephemeral=True
            )
            return

        game = self.active_games[interaction.guild_id]
        user_id = interaction.user.id

        # Check if user can reap
        can_reap, wait_time = game.can_reap(user_id)
        if not can_reap:
            await interaction.response.send_message(
                f"You must wait {wait_time} more seconds!",
                ephemeral=True
            )
            return

        # Process the reap
        reaped = game.reap(user_id)
        total_score = self.db.update_score(user_id, interaction.guild_id, reaped)

        # Check for win
        if total_score >= game.end:
            await interaction.channel.send(
                f"🎉 {interaction.user.mention} has won the game with a score of {total_score}!"
            )
            # Cleanup game
            if game.message_id:
                try:
                    msg = await interaction.channel.fetch_message(game.message_id)
                    await msg.unpin()
                except discord.NotFound:
                    pass  # Message might have been deleted
            del self.active_games[interaction.guild_id]
        
        await interaction.response.send_message(
            f"Reaped {reaped} seconds! Your current score is now {total_score}!"
        )

    @reaper_group.command(name="end", description="End the current Reaper game")
    @app_commands.describe(reason="Reason for ending the game")
    async def reaper_end(self, interaction: discord.Interaction, reason: str = None):
        """End the current Reaper game in the server."""
        if not any(role.name == config.ADMIN_ROLE for role in interaction.user.roles):
            await interaction.response.send_message(
                f"You need the '{config.ADMIN_ROLE}' role to end a game!",
                ephemeral=True
            )
            return

        if interaction.guild_id not in self.active_games:
            await interaction.response.send_message(
                "No game is currently running!",
                ephemeral=True
            )
            return

        game = self.active_games[interaction.guild_id]
        
        # Unpin start message
        if game.message_id:
            try:
                msg = await interaction.channel.fetch_message(game.message_id)
                await msg.unpin()
            except discord.NotFound:
                pass  # Message might have been deleted

        del self.active_games[interaction.guild_id]
        
        end_message = f"Game {game.game_number} ended by {interaction.user.mention}"
        if reason:
            end_message += f"\nReason: {reason}"
        await interaction.response.send_message(end_message)

    @reaper_group.command(name="leaderboard", description="Show the Reaper leaderboard")
    async def reaper_leaderboard(self, interaction: discord.Interaction):
        """Display the leaderboard for the server."""
        # Get top 10 scores
        top_scores = self.db.get_leaderboard(interaction.guild_id)
        
        # Get requester's score if not in top 10
        user_score = self.db.get_user_score(interaction.user.id, interaction.guild_id)

        embed = discord.Embed(
            title="Reaper Leaderboard",
            color=discord.Color.green()
        )
        
        # Add current game info if a game is running
        if interaction.guild_id in self.active_games:
            game = self.active_games[interaction.guild_id]
            embed.add_field(
                name="Current Game Info",
                value=f"Game #{game.game_number}\n"
                      f"Target: {game.end} seconds\n"
                      f"Cooldown: {game.cooldown} seconds\n"
                      f"Current Count: {game.count} seconds",
                inline=False
            )

        # Build leaderboard text
        leaderboard_text = ""
        user_in_top10 = False
        
        for rank, (user_id, score) in enumerate(top_scores, 1):
            if user_id == interaction.user.id:
                user_in_top10 = True
            try:
                user = await self.bot.fetch_user(user_id)
                username = user.name
            except discord.NotFound:
                username = f"Unknown User ({user_id})"
            leaderboard_text += f"{rank}. {username}: {score} seconds\n"

        embed.add_field(
            name="Top 10",
            value=leaderboard_text or "No scores yet!",
            inline=False
        )
        
        # Add user's score if they're not in top 10
        if user_score and not user_in_top10:
            embed.add_field(
                name="Your Score",
                value=f"{interaction.user.name}: {user_score} seconds",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ReaperCog(bot))