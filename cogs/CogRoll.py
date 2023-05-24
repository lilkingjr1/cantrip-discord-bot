"""CogRoll.py

Handles all commands associated with dice rolls and attacks.
Date: 05/12/2023
Authors: Scott Fisher, David Wolfe, Sinjin Serrano
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import random
import re

import discord
from discord.ext import commands

def parse_roll(dice_specs):
    roll_pattern = re.compile(r'(?P<num_dice>\d*)\s*d\s*(?P<dice_type>\d+)\s*(?P<modifier>[+-]\s*\d+)?')
    valid_dice_types = [4, 6, 8, 10, 12, 20, 100]
    results = []
    for dice_spec in dice_specs:
    # Parse the dice specification string using regex
        match = roll_pattern.match(dice_spec.strip())
        if not match:
            results.append('Invalid dice specification! Example Roll: (1d6+2, 3d 10 - 3)')
            continue
            
        # Extract number of dice, dice type, and modifier from regex match object
        num_dice = 1
        if (match.group('num_dice') != ''):
            num_dice = int(match.group('num_dice'))
        dice_type = int(match.group('dice_type'))
        modifier_str = match.group('modifier')
        modifier = int(modifier_str.replace(' ', '')) if modifier_str else 0
            
        # Check if dice type is valid
        if dice_type not in valid_dice_types:
            results.append('Invalid dice type! Valid Dice types: [4, 6, 8, 10, 12, 20]')
            continue

        # Roll the dice and compute total
        dice_rolls, total = roll_dice(num_dice, dice_type, modifier)
        results.append(create_result_string(dice_rolls, total, num_dice, dice_type, modifier, modifier_str))
    
    return results

def roll_dice(num_dice, dice_type, modifier):
        """Rolls the specified number of dice with the given type and modifier.
        
        Returns the list of dice rolls and the total sum.
        """
        dice_rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        total = sum(dice_rolls)
        if modifier:
            total += modifier
        return dice_rolls, total

def create_result_string(dice_rolls, total, num_dice, dice_type, modifier, modifier_str):
    modifier_str = f'{modifier_str.strip()}' if modifier_str else ''
    return f"You rolled {num_dice}d{dice_type}{modifier_str}: {dice_rolls} {'+' if modifier >= 0 else '-'} {abs(modifier)} = {total}"

class CogRoll(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Listener: On Cog Ready
        
        Runs when the cog is successfully cached within the Discord API.
        """
        print(f"{self.bot.get_datetime_str()}: [Roll] Successfully cached!")
        
    @discord.slash_command(name='roll', description='Rolls 1 or more of the following dice: [d4, d6, d8, d10, d12, d20, d100]')
    async def roll_dice_command(self, ctx, dice: discord.Option(str, description="Example Roll: (1d6+2, 3d 10 - 3)", max_length=255, required=True)):
        # Split the input by comma to separate multiple dice specifications
        dice_specs = dice.split(',')
        results = parse_roll(dice_specs)
        
        await ctx.respond('\n'.join(results))

def setup(bot):
    """Called by Pycord to setup the cog"""
    cog = CogRoll(bot)
    cog.guild_ids = [bot.guild_id]
    bot.add_cog(cog)
    