"""main.py

Main file to start Cantrip
Date: 05/14/2023
Authors: David Wolfe, Scott Fisher, Sinjin Serrano
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import os
import sys
from dotenv import load_dotenv

import discord
from discord.ext import commands
from src import CantripBot

from simplemysql import SimpleMysql

def main():
    # Print copyright notice
    print("Cantrip Discord Bot\n"
          "Copyright (c) 2023 Scott Fisher, Sinjin Serrano, & David Wolfe\n"
          "This program comes with ABSOLUTELY NO WARRANTY.\n"
          "This is free software, and you are welcome to redistribute it\n"
          "under certain conditions; see LICENSE file for details.\n")
    
    VERSION = "1.0.0"
    AUTHORS = "Scott Fisher\nSinjin Serrano\nDavid Wolfe"
    COGS_LIST = [
        "CogCharacters",
        "CogAttacks",
        "CogRoll",
        "CogAudio"
    ]

    # Load environment variables
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD_ID = os.getenv('GUILD_ID')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    try:
        GUILD_ID = int(GUILD_ID)
    except:
        print("ERROR: GUILD_ID parameter is missing or invalid!")
        print("\tPlease ensure this variable is set correctly in your environment or .env file.")
        sys.exit(2)

    # Database Initialization
    try:
        db = SimpleMysql(
            host=DB_HOST,
            port=DB_PORT,
            db=DB_NAME,
            user=DB_USER,
            passwd=DB_PASSWORD,
            autocommit=True,
            keep_alive=True
        )
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(3)


    """Discord Bot -- Main

    Pycord initialization, core functionality, and root slash commands.
    """
    # Create intents before creating bot instance
    intents = discord.Intents().default()
    intents.members = True
    intents.message_content = True
    # Setup activity of bot
    activity = discord.Activity(type=discord.ActivityType.playing, name="D&D 5e")
    
    # Create the bot object
    bot = CantripBot(TOKEN, GUILD_ID, db, intents=intents, activity=activity)

    # Add cogs to bot
    for cog in COGS_LIST:
        bot.load_extension(f'cogs.{cog}')
    
    @bot.event
    async def on_message(message):
        """Event: On Message
        
        Replies to 'good bot' messages directed at the bot.
        """
        if bot.user.mentioned_in(message):
            if 'good bot' in message.content.lower():
                await message.channel.send("Aww shucks!", reference=message)

    @bot.slash_command(guild_ids=[GUILD_ID], name = "about", description="Displays information about the Cantrip Bot.")
    @commands.cooldown(1, 60, commands.BucketType.user) # A single user can only call this every 60 seconds
    async def about(ctx):
        """Slash Command: /about
        
        Displays information about the Cantrip Bot.
        """
        _description = ('Cantrip is a Discord bot, written in Python using the Pycord API, with the goal of making the '
                        'popular tabletop game "Dungeons and Dragons 5th Edition" (D&D 5e) easier to organize and '
                        'play by providing a suite of organizational and planning tools.')
        _embed = discord.Embed(
            title="About:",
            description=_description,
            color=discord.Colour.blue()
        )
        _embed.set_author(
            name="Cantrip - An All-Purpose D&D Discord Bot", 
            icon_url="https://bitbucket.org/comp-350-2/cantrip-discord-bot/raw/a168d2e16fe99b7386af18d785bd5d001adbd9fb/icon.jpg"
        )
        _embed.set_thumbnail(url="https://bitbucket.org/comp-350-2/cantrip-discord-bot/raw/a168d2e16fe99b7386af18d785bd5d001adbd9fb/logo.jpg")
        # Construct string of bot commands for display
        _cmd_str = "```"
        for command in bot.commands:
            _cmd_str += f"/{command}\n"
        _cmd_str += "```"
        _embed.add_field(name="Commands:", value=_cmd_str, inline=True)
        _embed.add_field(name="Authors:", value=AUTHORS, inline=True)
        _embed.add_field(name="Version:", value=VERSION, inline=True)
        _embed.set_footer(text=f"Bot latency is {bot.latency}")
        await ctx.respond(embed=_embed)

    @bot.slash_command(guild_ids=[GUILD_ID], name = "shutdown", description="Cleanly shuts Cantrip down. Only admins can do this.")
    @discord.default_permissions(administrator=True) # Only members with admin can use this command.
    async def shutdown(ctx):
        """Slash Command: /shutdown
        
        Cleanly shuts Cantrip down. Only admins can do this.
        """
        print(f"{bot.get_datetime_str()}: [Shutdown] Shutdown command issued by {ctx.author.name}#{ctx.author.discriminator}.")
        await ctx.respond("Goodbye.")
        await bot.close()

    # Attempt to start the bot
    print(f"{bot.get_datetime_str()}: [Startup] Bot attempting to login to Discord...")
    try:
        bot.run(bot.token)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
