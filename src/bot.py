"""bot.py

A subclass of `discord.Bot` that adds ease-of-use instance variables and functions (e.g. database object).
Date: 04/25/2023
Authors: David Wolfe
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

from datetime import datetime

import discord
from discord.ext import commands

class CantripBot(discord.Bot):
    def __init__(self, token, guild_id, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token
        self.guild_id = guild_id
        self.db = db
    
    async def on_ready(self):
        """Event: On Ready
        
        Called when the bot successfully connects to the API and becomes online.
        Excessive API calls in this function should be avoided.
        """
        # Check that guild_id is valid
        _guild = self.get_guild(self.guild_id)
        if _guild == None:
            print(f"ERROR: Could not find valid guild with ID: {self.guild_id}")
            await self.close()
        
        print(f"{self.get_datetime_str()}: [Startup] {self.user} is ready and online!")
    
    async def on_application_command_error(self, ctx, error):
        """Event: On Command Error
        
        Required for command cooldown failures.
        """
        if isinstance(error, commands.CommandError):
            await ctx.respond(error, ephemeral=True)
        else:
            raise error
    
    def get_datetime_str(self) -> str:
        """Return a formatted datetime string for logging"""
        _now = datetime.now()
        return _now.strftime("%m/%d/%Y %H:%M:%S")
