"""bot.py

Main Discord bot file
Date: 04/14/2023
Authors: David Wolfe, Scott Fisher
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import os
from dotenv import load_dotenv
from datetime import datetime

import inflect
import discord
from discord.ext import commands
from simplemysql import SimpleMysql

load_dotenv()
VERSION = "0.0.2"
AUTHORS = "Scott Fisher\nRichard Roa\nSinjin Serrano\nDavid Wolfe"
TOKEN = str(os.getenv('DISCORD_TOKEN'))
GUILD_ID = int(os.getenv('GUILD_ID'))
DB_HOST = str(os.getenv('DB_HOST'))
DB_PORT = str(os.getenv('DB_PORT'))
DB_USER = str(os.getenv('DB_USER'))
DB_PASSWORD = str(os.getenv('DB_PASSWORD'))
DB_NAME = str(os.getenv('DB_NAME'))


def get_datetime_str():
    """Return a formatted datetime string for logging"""
    _now = datetime.now()
    return _now.strftime("%m/%d/%Y %H:%M:%S")


# Print copyright notice
print("Cantrip Discord Bot\n"
      "Copyright (c) 2023 Scott Fisher, Richard Roa, Sinjin Serrano, & David Wolfe\n"
      "This program comes with ABSOLUTELY NO WARRANTY.\n"
      "This is free software, and you are welcome to redistribute it\n"
      "under certain conditions; see LICENSE file for details.\n")

# Setup Inflect engine
p = inflect.engine()

# Database Initialization
db = SimpleMysql(
    host=DB_HOST,
    port=DB_PORT,
    db=DB_NAME,
    user=DB_USER,
    passwd=DB_PASSWORD,
    keep_alive=True
)


"""Discord Bot -- Main

Pycord initialization, core functionality, and root slash commands.
"""
print(f"{get_datetime_str()}: [Startup] Bot attempting to login to Discord...")

# Create intents before creating bot instance
intents = discord.Intents().default()
intents.members = True
intents.message_content = True
# Setup activity of bot
activity = discord.Activity(type=discord.ActivityType.playing, name="D&D 5e")
# Create the bot object
bot = discord.Bot(intents=intents, activity=activity)
# Add cogs to bot
""" Future TODO """

@bot.event
async def on_ready():
    """Event: On Ready
    
    Called when the bot successfully connects to the API and becomes online.
    Excessive API calls in this function should be avoided.
    """
    print(f"{get_datetime_str()}: [Startup] {bot.user} is ready and online!")
    
    # Initialize and get global guild object
    global guild
    guild = bot.get_guild(GUILD_ID)
    if guild == None:
        print(f"ERROR: Could not find valid guild with ID: {GUILD_ID}")
        await bot.close()

@bot.event
async def on_application_command_error(ctx, error):
    """Event: On Command Error
    
    Required for command cooldown failures.
    """
    if isinstance(error, commands.CommandError):
        await ctx.respond(error, ephemeral=True)
    else:
        raise error

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
    _embed.set_author(name="Cantrip - An All-Purpose D&D Discord Bot", icon_url="https://cdn.discordapp.com/app-icons/1083520537017462824/6fc4107a9d1ddf3f164d48c26b56d324.png")
    _embed.set_thumbnail(url="https://cdn.discordapp.com/app-icons/1083520537017462824/6fc4107a9d1ddf3f164d48c26b56d324.png")
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
    print(f"{get_datetime_str()}: [Shutdown] Shutdown command issued by {ctx.author.name}#{ctx.author.discriminator}.")
    await ctx.respond("Goodbye.")
    await bot.close()

# Start the bot
bot.run(TOKEN)
