"""CogCharacters.py

Handles all commands associated with creating, retrieving, editing, and deleting player characters from the database.
Date: 05/05/2023
Authors: David Wolfe, Sinjin Serrano
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import os
import re
import json
from datetime import datetime

import discord
from discord.ext import commands


DEFAULT_PORTRAIT_URL = "https://bitbucket.org/comp-350-2/cantrip-discord-bot/raw/947ae7ddbb6e2396ee55864c991e5a2935331ee6/assets/default_portrait.png"
MAX_CHARACTERS = 5
CMD_COOLDOWN = 10 # Seconds
EXPORT_DEFAULT = 'export.json'
CHARACTER_ATTRIBUTES = [
    "name", 
    "created", 
    "level", 
    "initiative", 
    "strength", 
    "dexterity", 
    "constitution", 
    "intelligence", 
    "wisdom", 
    "charisma", 
    "proficiencies", 
    "race", 
    "class", 
    "portrait"
]
ATTACK_PROPERTIES = [
    'aid',
    'cid',
    'name',
    'attack_roll',
    'saving_throw',
    'attribute',
    'target',
    'proficient',
    'modifiers',
    'damage_roll'
]
SKILL_STRINGS = (
    "Acrobatics", 
    "Animal Handling", 
    "Arcana", 
    "Athletics", 
    "Deception", 
    "History", 
    "Insight", 
    "Intimidation", 
    "Investigation", 
    "Medicine", 
    "Nature", 
    "Perception", 
    "Performance", 
    "Persuasion", 
    "Religion", 
    "Sleight of Hand", 
    "Stealth", 
    "Survival"
)
# Create tuple from skill strings without capitals or spaces for functional calls
SKILLS = tuple(value.lower().replace(" ", "") for value in SKILL_STRINGS)


async def get_player_characters(ctx: discord.AutocompleteContext):
    """Autocomplete Context: Get player characters
    
    Returns array of character names a user owns.
    """
    _dbEntries = ctx.bot.db.getAll(
        "characters", 
        ["name"], 
        ("uid=%s", [ctx.interaction.user.id])
    )
    if _dbEntries:
        return [character['name'] for character in _dbEntries]
    else:
        return []


class CogCharacters(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        #self.bot.db.query("DROP TABLE characters") # DEBUGGING
        self.bot.db.query(
            "CREATE TABLE IF NOT EXISTS characters ("
                "cid INT AUTO_INCREMENT PRIMARY KEY, "
                "uid BIGINT NOT NULL, "
                "name TINYTEXT NOT NULL, "
                "created DATE NOT NULL, "
                "level INT NOT NULL, "
                "initiative INT NOT NULL, "
                "strength INT NOT NULL, "
                "dexterity INT NOT NULL, "
                "constitution INT NOT NULL, "
                "intelligence INT NOT NULL, "
                "wisdom INT NOT NULL, "
                "charisma INT NOT NULL, "
                f"proficiencies SET{SKILLS}, "
                "race TINYTEXT, "
                "class TINYTEXT, "
                "portrait TINYTEXT NOT NULL"
            ")"
        )
    

    @commands.Cog.listener()
    async def on_ready(self):
        """Listener: On Cog Ready
        
        Runs when the cog is successfully cached within the Discord API.
        """
        print(f"{self.bot.get_datetime_str()}: [Characters] Successfully cached!")
    


    async def set_character_attribute(self, uid: int, character: str, attribute: str, value) -> bool:
        """Set Character Attribute
        
        Edits the attribute of a given user ID and character name.
        """
        _dbEntry = self.bot.db.getOne(
            "characters", 
            ["cid"], 
            ("uid=%s and name=%s", [uid, character])
        )
        if _dbEntry:
            self.bot.db.update(
                "characters",
                {attribute: value},
                [f"cid={_dbEntry['cid']}"]
            )
            return True
        else:
            return False
    
    def format_proficiencies_sql(self, proficiencies: str) -> tuple:
        """Format Proficiencies for MySQL
        
        Sanitizes input proficiencies string.
        Then, formats it as a single string tuple, because that matches the MySQL SET data type format.
        """
        if not proficiencies:
            return None
        proficiencies = proficiencies.lower()
        proficiencies = re.sub(r'[^a-z,]', '', proficiencies) # Remove everything except letters and commas
        proficiencies = (f'{proficiencies}')
        return proficiencies
    
    def sanitize_image_url(self, url: str) -> tuple:
        """Sanitize Image URL
        
        Checks if the input string is a valid image URL.
        If it is, will return True and the URL.
        If it's not, will return False and DEFAULT_PORTRAIT_URL
        """
        # Regular expression pattern to match an image URL
        image_url_pattern = re.compile(r'(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|jpeg|png|gif|bmp|tiff|webp)')
    
        # Check if the input string matches the image URL pattern
        if url and image_url_pattern.match(url):
            return True, url
        else:
            return False, DEFAULT_PORTRAIT_URL
    
    
    """Slash Command Group: /character
    
    A group of commands related to managing player characters.
    """
    character = discord.SlashCommandGroup("character", "Manage player characters")


    @character.command(name = "create", description="Create a new player character for yourself")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def create(
        self, 
        ctx, 
        name: discord.Option(str, description="Character name", max_length=255, required=True), 
        level: discord.Option(int, description="Character level", min_value=1, max_value=20, required=True), 
        initiative: discord.Option(int, description="Initiative modifier", min_value=-20, max_value=20, required=True), 
        strength: discord.Option(int, description="Strength ability score", min_value=1, max_value=30, required=True), 
        dexterity: discord.Option(int, description="Dexterity ability score", min_value=1, max_value=30, required=True), 
        constitution: discord.Option(int, description="Constitution ability score", min_value=1, max_value=30, required=True), 
        intelligence: discord.Option(int, description="Intelligence ability score", min_value=1, max_value=30, required=True), 
        wisdom: discord.Option(int, description="Wisdom ability score", min_value=1, max_value=30, required=True), 
        charisma: discord.Option(int, description="Charisma ability score", min_value=1, max_value=30, required=True), 
        proficiencies: discord.Option(str, description="Comma seperated list of skills you are proficient in (e.g. 'Acrobatics, Animal Handling')", max_length=255, required=False), 
        race: discord.Option(str, description="(Optional) Character's race", max_length=255, required=False), 
        c_class: discord.Option(str, name="class", description="(Optional) Character's class", max_length=255, required=False), 
        portrait: discord.Option(str, description="(Optional) URL to image of character portrait", max_length=255, required=False)
    ):
        """Slash Command: /character create
        
        Creates a new player character in the database for the author.
        """
        _success_str = f':white_check_mark: Character "{name}" has successfully been created!'
        _info_str = 'You can use other `/character ...` commands to view, edit, or delete your characters if you wish.'
        _name = name
        _date = datetime.now().date()
        proficiencies = self.format_proficiencies_sql(proficiencies)
        portrait = self.sanitize_image_url(portrait)[1]
        
        # Check for characters saved maximium
        _characters = await get_player_characters(ctx)
        if len(_characters) < MAX_CHARACTERS:
            # Check for exsiting character name in DB
            if _name in _characters:
                _name = name + ' Jr.'
                # Keep adding 'Jr.' if multiple duplicates
                while _name in _characters:
                    _name = _name + ' Jr.'
                _success_str = f':white_check_mark: Character "{_name}" has successfully been created!\n(You already had a character named {name}, so a next of kin was created)'
            
            self.bot.db.insert(
                "characters",
                {"uid": ctx.author.id, 
                 "name": _name, 
                 "created": _date, 
                 "level": level, 
                 "initiative": initiative, 
                 "strength": strength, 
                 "dexterity": dexterity, 
                 "constitution": constitution, 
                 "intelligence": intelligence, 
                 "wisdom": wisdom, 
                 "charisma": charisma, 
                 "proficiencies": proficiencies, 
                 "race": race, 
                 "class": c_class, 
                 "portrait": portrait}
            )
        else:
            _success_str = f':warning: Sorry! You can only have {MAX_CHARACTERS} characters saved at a time.'
        await ctx.respond(_success_str + '\n\n' + _info_str, ephemeral=True)
    
    @character.command(name = "view", description="Display basic info about one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def create(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to view", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        )
    ):
        """Slash Command: /character view
        
        Displays basic info about the author's chosen player character publicly.
        """
        _dbEntry = self.bot.db.getOne(
            "characters", 
            CHARACTER_ATTRIBUTES, 
            ("uid=%s and name=%s", [ctx.author.id, character])
        )
        if _dbEntry:
            _embed = discord.Embed(
                title=_dbEntry['name'],
                description=f"Level {_dbEntry['level']} {_dbEntry['race'] or ''} {_dbEntry['class'] or ''}\n",
                color=discord.Colour.dark_red()
            )
            _embed.set_author(
                name=f"{ctx.author.display_name}'s Character Sheet", 
                icon_url=ctx.author.avatar.url
            )
            _embed.set_thumbnail(url="https://bitbucket.org/comp-350-2/cantrip-discord-bot/raw/1e3af2deeecf8f8134cda012b7dc92026b59bfc5/assets/character_sheet_mini.jpg")
            _embed.add_field(name="Initiative:", value=_dbEntry['initiative'], inline=False)
            _embed.add_field(name="Strength:", value=_dbEntry['strength'], inline=True)
            _embed.add_field(name="Dexterity:", value=_dbEntry['dexterity'], inline=True)
            _embed.add_field(name="Constitution:", value=_dbEntry['constitution'], inline=True)
            _embed.add_field(name="Intelligence:", value=_dbEntry['intelligence'], inline=True)
            _embed.add_field(name="Wisdom:", value=_dbEntry['wisdom'], inline=True)
            _embed.add_field(name="Charisma:", value=_dbEntry['charisma'], inline=True)
            # Reconstruct proficient skills from database back into a pretty, comma-seperated, alphabetized string
            if _dbEntry['proficiencies']:
                _proficient_skills = [SKILL_STRINGS[SKILLS.index(skill)] for skill in _dbEntry['proficiencies']]
                _proficient_skills = sorted(_proficient_skills)
                _proficient_skills = ", ".join(_proficient_skills)
                _embed.add_field(name="Proficient Skills:", value=_proficient_skills, inline=False)
            _embed.set_image(url=_dbEntry['portrait'])
            _embed.set_footer(text=f"Created on {_dbEntry['created'].strftime('%m/%d/%Y')}")
            await ctx.respond(embed=_embed)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)
    
    @character.command(name = "delete", description="Delete one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def delete(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to delete", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        )
    ):
        """Slash Command: /character delete
        
        Deletes one of the author's chosen player characters (and associated attacks), with confirmation button.
        """
        _dbEntry = self.bot.db.getOne(
            "characters", 
            ["cid"], 
            ("uid=%s and name=%s", [ctx.author.id, character])
        )
        if _dbEntry:
            await ctx.respond(
                f'Are you absolutely sure you want to delete "{character}"?', 
                view=self.DeleteCharacter(_dbEntry, character), 
                ephemeral=True
            )
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)
    
    class DeleteCharacter(discord.ui.View):
        """Discord UI View: Delete Character Button
        
        Helper class.
        Displays verification button that will actually perform the character deletion.
        """
        def __init__(self, dbEntry, name, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.dbEntry = dbEntry
            self.name = name
        
        @discord.ui.button(label="Yes, I'm sure!", style=discord.ButtonStyle.danger, emoji="⚠")
        async def button_callback(self, button, interaction):
            interaction.client.db.delete(
                "characters", 
                ("cid = %s", [self.dbEntry['cid']])
            )
            interaction.client.db.delete(
                "attacks", 
                ("cid = %s", [self.dbEntry['cid']])
            )
            await interaction.response.edit_message(
                content=f':white_check_mark: Character "{self.name}" has successfully been deleted!', 
                view = None
            )
            
    @character.command(name = "export", description="Export one of your player characters in JSON format.")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def export(
        self,
        ctx,
        character: discord.Option(
            str, 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            description="Name of character to export", 
            max_length=255, 
            required=True
        )
    ):
        """Slash Command: /character export

        Exports a character sheet in JSON format.
        """
        _dbEntry = self.bot.db.getOne(
            "characters", 
            ["cid"] + CHARACTER_ATTRIBUTES, 
            ("uid=%s and name=%s", [ctx.author.id, character])
        )
        if _dbEntry:
            _atkEntry = self.bot.db.getAll(
                "attacks", 
                ATTACK_PROPERTIES, 
                ("cid=%s", [_dbEntry['cid']])
            )

            export = {
                "character_sheet": _dbEntry,
                "attacks_sheet": _atkEntry
            }

            # Generate JSON file
            with open(EXPORT_DEFAULT, 'w') as file:
                file.write(json.dumps(export, default=str, indent=4))
            
            # Upload generated file
            await ctx.respond(file=discord.File(EXPORT_DEFAULT), ephemeral=True)

            # Remove generated file
            if os.path.exists(EXPORT_DEFAULT):
                os.remove(EXPORT_DEFAULT)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)
    
    
    """Slash Command Sub-Group: /character edit
    
    A sub-group of commands related to editing player characters.
    """
    edit = character.create_subgroup("edit", "Edit an attribute of one of your player characters")


    @edit.command(name = "name", description="Edit the name of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def name(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        name: discord.Option(
            str, 
            description="New name", 
            max_length=255, 
            required=True
        )
    ):
        """Slash Command: /character edit name
        
        Edits the name of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "name", name):
            await ctx.respond(f':white_check_mark: Successfully changed {character}\'s name to "{name}"!', ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "level", description="Edit the level of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def level(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        level: discord.Option(
            int, 
            description="New level", 
            min_value=1, 
            max_value=20, 
            required=True
        )
    ):
        """Slash Command: /character edit level
        
        Edits the level of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "level", level):
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s level to {level}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "initiative", description="Edit the initiative modifier of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def initiative(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        initiative: discord.Option(
            int, 
            description="New initiative modifier", 
            min_value=-20, 
            max_value=20, 
            required=True
        )
    ):
        """Slash Command: /character edit initiative
        
        Edits the initiative modifier of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "initiative", initiative):
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s initiative modifier to {initiative}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "strength", description="Edit the strength ability score of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def strength(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        strength: discord.Option(
            int, 
            description="New strength ability score", 
            min_value=1, 
            max_value=30, 
            required=True
        )
    ):
        """Slash Command: /character edit strength
        
        Edits the strength ability score of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "strength", strength):
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s strength ability score to {strength}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "dexterity", description="Edit the dexterity ability score of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def dexterity(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        dexterity: discord.Option(
            int, 
            description="New dexterity ability score", 
            min_value=1, 
            max_value=30, 
            required=True
        )
    ):
        """Slash Command: /character edit dexterity
        
        Edits the dexterity ability score of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "dexterity", dexterity):
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s dexterity ability score to {dexterity}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "constitution", description="Edit the constitution ability score of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def constitution(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        constitution: discord.Option(
            int, 
            description="New constitution ability score", 
            min_value=1, 
            max_value=30, 
            required=True
        )
    ):
        """Slash Command: /character edit constitution
        
        Edits the constitution ability score of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "constitution", constitution):
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s constitution ability score to {constitution}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "intelligence", description="Edit the intelligence ability score of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def intelligence(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        intelligence: discord.Option(
            int, 
            description="New intelligence ability score", 
            min_value=1, 
            max_value=30, 
            required=True
        )
    ):
        """Slash Command: /character edit intelligence
        
        Edits the intelligence ability score of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "intelligence", intelligence):
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s intelligence ability score to {intelligence}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "wisdom", description="Edit the wisdom ability score of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def wisdom(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        wisdom: discord.Option(
            int, 
            description="New wisdom ability score", 
            min_value=1, 
            max_value=30, 
            required=True
        )
    ):
        """Slash Command: /character edit wisdom
        
        Edits the wisdom ability score of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "wisdom", wisdom):
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s wisdom ability score to {wisdom}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "charisma", description="Edit the charisma ability score of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def charisma(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        charisma: discord.Option(
            int, 
            description="New charisma ability score", 
            min_value=1, 
            max_value=30, 
            required=True
        )
    ):
        """Slash Command: /character edit charisma
        
        Edits the charisma ability score of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "charisma", charisma):
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s charisma ability score to {charisma}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "proficiencies", description="Edit the skill proficiencies of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def proficiencies(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        proficiencies: discord.Option(
            str, 
            description="New comma seperated list of skills you are proficient in (e.g. 'Acrobatics, Animal Handling')", 
            max_length=255, 
            required=False
        )
    ):
        """Slash Command: /character edit proficiencies
        
        Edits the skill proficiencies of one of the author's chosen player characters.
        """
        proficiencies = self.format_proficiencies_sql(proficiencies)
        if await self.set_character_attribute(ctx.author.id, character, "proficiencies", proficiencies):
            _dbEntry = self.bot.db.getOne(
                "characters", 
                ["proficiencies"], 
                ("uid=%s and name=%s", [ctx.author.id, character])
            )
            # Reconstruct proficient skills from database back into a pretty, comma-seperated, alphabetized string
            _proficient_skills = None
            if _dbEntry['proficiencies']:
                _proficient_skills = [SKILL_STRINGS[SKILLS.index(skill)] for skill in _dbEntry['proficiencies']]
                _proficient_skills = sorted(_proficient_skills)
                _proficient_skills = ", ".join(_proficient_skills)
            await ctx.respond(f":white_check_mark: Successfully changed {character}'s skill proficiencies to {_proficient_skills}!", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "race", description="Edit the race of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def race(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        race: discord.Option(
            str, 
            description="New race", 
            max_length=255, 
            required=False
        )
    ):
        """Slash Command: /character edit race
        
        Edits the race of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "race", race):
            await ctx.respond(f':white_check_mark: Successfully changed {character}\'s race to "{race}"!', ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "class", description="Edit the class of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def c_class(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        c_class: discord.Option(
            str, 
            name="class", 
            description="New class", 
            max_length=255, 
            required=False
        )
    ):
        """Slash Command: /character edit class
        
        Edits the class of one of the author's chosen player characters.
        """
        if await self.set_character_attribute(ctx.author.id, character, "class", c_class):
            await ctx.respond(f':white_check_mark: Successfully changed {character}\'s class to "{c_class}"!', ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

    @edit.command(name = "portrait", description="Edit the portrait image URL of one of your player characters")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def portrait(
        self,
        ctx,
        character: discord.Option(
            str, 
            description="Name of character to edit", 
            autocomplete=discord.utils.basic_autocomplete(get_player_characters), 
            max_length=255, 
            required=True
        ),
        portrait: discord.Option(
            str, 
            description="New portrait image URL", 
            max_length=255, 
            required=False
        )
    ):
        """Slash Command: /character edit portrait
        
        Edits the portrait image URL of one of the author's chosen player characters.
        """
        portrait = self.sanitize_image_url(portrait)
        if await self.set_character_attribute(ctx.author.id, character, "portrait", portrait[1]):
            if portrait[0]:
                await ctx.respond(f":white_check_mark: Successfully changed {character}'s portrait to:\n{portrait[1]}", ephemeral=True)
            else:
                await ctx.respond(f"Image URL is either empty or not valid.\nChanged {character}'s portrait to a default image.", ephemeral=True)
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)
        
def setup(bot):
    """Called by Pycord to setup the cog"""
    cog = CogCharacters(bot)
    cog.guild_ids = [bot.guild_id]
    bot.add_cog(cog)
