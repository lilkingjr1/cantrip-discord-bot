"""CogAttacks.py

Handles all attacks associated with player characters from the database.
Date: 04/18/2023
Authors: David Wolfe, Scott Fisher
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import os
from dotenv import load_dotenv
from datetime import datetime

import discord
from discord.ext import commands

load_dotenv()
GUILD_ID = int(os.getenv('GUILD_ID'))


class CogAttacks(discord.Cog, guild_ids=[GUILD_ID]):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        #self.db.query("DROP TABLE characters") # DEBUGGING
        self.db.query(
            "CREATE TABLE IF NOT EXISTS attacks ("
                "aid INT AUTO_INCREMENT PRIMARY KEY, "
                "cid INT FOREIGN KEY REFERENCES characters(cid), "
                "uid BIGINT NOT NULL, "
                "hit INT NOT NULL, "
                "damage TINYTEXT NOT NULL, "
                "type TINYTEXT"
            ")"
        )
