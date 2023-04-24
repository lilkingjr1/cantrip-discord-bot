"""CogRoll.py

Handles all commands associated with dice rolls and attacks.
Date: 04/24/2023
Authors: Scott Fisher, David Wolfe
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import os
import random
import discord
from dotenv import load_dotenv
from datetime import datetime
from discord.ext import commands

load_dotenv()
GUILD_ID = int(os.getenv('GUILD_ID'))

def get_datetime_str():
    """Return a formatted datetime string for logging"""
    _now = datetime.now()
    return _now.strftime("%m/%d/%Y %H:%M:%S")


class CogRoll(discord.Cog, guild_ids=[GUILD_ID]):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        print(f"{get_datetime_str()}: [Roll] Successfully loaded!")

    @discord.slash_command(name='roll', description='Rolls 1 or more of the following dice: [d4, d6, d8, d10, d12, d20]')
    async def roll_dice(self, ctx, dice_spec: str):
        # Parse the dice specification string (e.g. "2d6+2" or "2d6-2") into number_of_dice, dice_type, and modifier variables
        try:
            dice_parts = dice_spec.split('d')
            number_of_dice = int(dice_parts[0])
            if '+' in dice_parts[1]:
                dice_type, modifier = map(int, dice_parts[1].split('+'))
                operator = '+'
            elif '-' in dice_parts[1]:
                dice_type, modifier = map(int, dice_parts[1].split('-'))
                operator = '-'
            else:
                dice_type = int(dice_parts[1])
                modifier = 0
                operator = '+'
        except (ValueError, IndexError):
            await ctx.respond('Invalid dice specification. Usage: /roll <number of dice>d<dice type>[+/-<modifier>]', ephemeral=True)
            return
        
        # Roll the dice and compute total
        if dice_type in [4, 6, 8, 10, 12, 20]:
            dice_rolls = [random.randint(1, dice_type) for _ in range(number_of_dice)]
            total = sum(dice_rolls)
            if operator == '+':
                total += modifier
            else:
                total -= modifier
            modifier_str = f'{operator}{modifier}' if operator == '-' or modifier >= 0 else f'+{modifier}'
            await ctx.respond(f"You rolled {number_of_dice}d{dice_type}{modifier_str}: {dice_rolls} {operator} {modifier} = {total}")
        else:
            await ctx.respond('Invalid dice type. Available types: 4, 6, 8, 10, 12, 20', ephemeral=True)
          