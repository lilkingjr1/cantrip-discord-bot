"""CogAttacks.py

Handles all attacks associated with player characters from the database.
Date: 05/05/2023
Authors: David Wolfe, Scott Fisher, Sinjin Serrano
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import discord
from discord.ext import commands

from cogs.CogCharacters import get_player_characters

ATTRIBUTES = [
    'Strength',
    'Dexterity',
    'Constitution',
    'Intelligence',
    'Wisdom',
    'Charisma'
]

class CogAttacks(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        #self.bot.db.query("DROP TABLE attacks") # DEBUGGING
        self.bot.db.query(
            "CREATE TABLE IF NOT EXISTS attacks ("
                "aid INT AUTO_INCREMENT PRIMARY KEY, "      # ID of attack in table 'attacks'
                "cid INT NOT NULL, "                                 # (foreign key) ID of attack's owner in table 'characters'
                #"FOREIGN KEY (cid)"
                #    "REFERENCES characters(cid), "
                "name TINYTEXT NOT NULL, "                  # name of attack
                "attack_roll BOOL NOT NULL, "               # does that attack need an attack roll?
                "saving_throw BOOL NOT NULL, "              # does the attack need a saving throw?
                "attribute TINYTEXT, "                      # which ability is the attack calculated with (typically STR or DEX)
                "target TINYTEXT, "                         # which ability is the saving throw made with?
                "proficient BOOL NOT NULL, "                # are they proficient with this attack?
                "modifiers INT NOT NULL, "                  # additional modifiers (i.e. +1 weapons, bonus to spell attacks or save DCs)
                "damage_roll TINYTEXT NOT NULL"             # damage roll calculation, to be parsed by the CogRolls (i.e. 8d6, 1d8+2d6)
            ")"
        )

    @commands.Cog.listener()
    async def on_ready(self):
        """Listener: On Cog Ready
        
        Runs when the cog is successfully cached within the Discord API.
        """
        print(f"{self.bot.get_datetime_str()}: [Attacks] Successfully cached!")
    
    
    """Slash Command Group: /attack
    
    Commands for managing attacks. Having a character is a prerequisite for making attacks.
    """
    attack = discord.SlashCommandGroup("attack", "Manage attacks")

    @attack.command(name = "add", description="Add an attack to a character's repetoire.")
    async def create(
        self,
        ctx,
        character: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(get_player_characters),
            description="Which character is adding an attack?",
            max_length=255,
            required=True
        ),
        name: discord.Option(
            str,
            description="Name of the attack you are creating.",
            max_length=255,
            required=True
        )
    ):
        """Slash Command: /attack add
        
        Adds an attack to the specified character:
         - character: string of the attack's character (autocompleted)
         - name: string of the attack's name
        """
        _dbEntry = self.bot.db.getOne(
            "characters",
            ["cid"],
            ("uid=%s and name=%s", [ctx.author.id, character])
        )
        if _dbEntry:
            await ctx.respond(
                "Creating {}: {}".format(character, name),
                view=AttackView(_dbEntry['cid'], character, name),
                ephemeral=True
            )
        else:
            await ctx.respond(f'You do not have a character named "{character}"', ephemeral=True)

class AttackTypeDropdown(discord.ui.Select):
    """Dropdown menu for the attack's type.
    
    Allows the user to select whether the attack requires an attack roll and/or saving throw.
    While the user can technically select 'Neither' and the other two rolls, logic will check
    for the presence of 'Neither', making it supercede the other two.
    """
    def __init__(self, character, name):
        self.types=[
            discord.SelectOption(
                label="Attack Roll",
                description="The caster's attack roll (d20) is needed for this attack.",
            ),
            discord.SelectOption(
                label="Saving Throw",
                description="The target needs to make a saving throw.",
            ),
            discord.SelectOption(
                label="Neither",
                description="No attack roll needed (i.e. Magic Missile).",
            )
        ]
        super().__init__(row = 0, placeholder="Select rolls for {}'s [{}]?".format(character, name), options=self.types, max_values=2)

class AttrButton(discord.ui.Button):
    """
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class DamageModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(title="Modifiers and damage roll", *args, **kwargs)
        
    
    def initialize(self, neither=True):
        if not neither:
            self.add_item(discord.ui.InputText(label="ATTACK ROLL / SAVE DC MODIFIERS"))
        self.add_item(discord.ui.InputText(label="DAMAGE ROLL"))


class AttackView(discord.ui.View):
    """View for the attack type dropdown menu.
    """
    def __init__(self, cid, character='placeholder', name='placeholder'):
        super().__init__()
        self.character = character
        self.cid = cid
        self.name = name
        self.types = []
        self.attr = ATTRIBUTES[0]   # attack's attribute
        self.target = ATTRIBUTES[0] # attack's target attribute (i.e. Dexterity Saving Throw for Fireball)
        self.proficient = False
        self.modifiers = 0
        self.damage_roll = ''
        self.dropdown = AttackTypeDropdown(self.character, self.name)
        self.attr_buttons = [
            AttrButton(label=attr, style=discord.ButtonStyle.primary, custom_id=attr, row=1)
            for attr in ATTRIBUTES if attr != 'Constitution'
        ]
        self.target_buttons = [
            AttrButton(label=attr, style=discord.ButtonStyle.primary, custom_id=(attr + '_target'), row=None)
            for attr in ATTRIBUTES
        ]
        self.confirm_buttons = [
            AttrButton(label='Yes', style=discord.ButtonStyle.primary, custom_id='Yes', row=4),
            AttrButton(label='No', style=discord.ButtonStyle.primary, custom_id='No', row=4)
        ]
        self.input_modal = DamageModal()
        self.prompt_attack_type()
    
    
    
    async def type_callback(self, interaction):
        self.dropdown.disabled = True
        # Copy the selection into this object's data
        self.types = self.dropdown.values.copy()
        if 'Neither' in self.types:
            self.types = ['Neither']
        # Lock in selection
        if "Neither" in self.types:
            self.dropdown.placeholder="No attack roll needed"
        elif "Attack Roll" in self.types and "Saving Throw" in self.types:
            self.dropdown.placeholder="Attack Roll and Saving Throw"
        elif "Attack Roll" in self.types:
            self.dropdown.placeholder="Attack Roll"
        elif "Saving Throw" in self.types:
            self.dropdown.placeholder="Saving Throw"
        else:
            self.dropdown.placeholder="you shouldn't see this"
        if "Neither" not in self.types:
            self.prompt_attack_attr()
        else:
            self.prompt_is_proficient()
        await interaction.response.edit_message(content="**Select the attack's attribute.**", view=self)

    async def attr_callback(self, interaction):
        self.attr = interaction.custom_id
        # Disable all buttons in list "attr_buttons"
        for b in self.attr_buttons:
            if b.label == self.attr:
                b.style = discord.ButtonStyle.success
            b.disabled = True
        # Prompt Next Step
        if 'Saving Throw' in self.types:
            self.prompt_save_target()
        else:
            self.prompt_is_proficient()
        await interaction.response.edit_message(content="**Select attribute of saving throw.**", view=self)
    
    async def target_callback(self, interaction):
        self.target = interaction.custom_id[:-len('_target')]
        # Disable all buttons in list "target_buttons"
        for b in self.target_buttons:
            if b.label == self.target:
                b.style = discord.ButtonStyle.success
            b.disabled = True
        # Prompt Next Step
        self.prompt_is_proficient()
        await interaction.response.edit_message(content="**Are you proficient in this attack?**", view=self)

    async def confirm_callback(self, interaction):
        self.proficient = interaction.custom_id == 'Yes'
        # Disable all Yes/No buttons
        for b in self.confirm_buttons:
            if b.label == interaction.custom_id:
                b.style = discord.ButtonStyle.success
            b.disabled = True
        # Prompt Next Step
        
        await self.prompt_damage_and_modifiers(interaction)
    
    async def modal_callback(self, interaction):
        await interaction.response.edit_message(content="Created {}'s {}!".format(self.character, self.name), view=self)
        if 'Neither' in self.types:
            self.damage_roll = self.input_modal.children[0].value
        else:
            self.modifiers = self.input_modal.children[0].value
            self.damage_roll = self.input_modal.children[1].value
        await self.insert_attack(interaction)
    
    def prompt_attack_type(self):
        self.dropdown.callback = self.type_callback
        self.add_item(self.dropdown)
    
    def prompt_attack_attr(self):
        for b in self.attr_buttons: 
            b.callback = self.attr_callback
            self.add_item(b)

    def prompt_save_target(self):
        for b in self.target_buttons:
            b.callback = self.target_callback
            self.add_item(b)
    
    def prompt_is_proficient(self):
        for b in self.confirm_buttons:
            b.callback = self.confirm_callback
            self.add_item(b)
    
    async def prompt_damage_and_modifiers(self, interaction):
        self.input_modal.callback = self.modal_callback
        self.input_modal.initialize('Neither' in self.types)
        await interaction.response.send_modal(self.input_modal)
    
    def return_data(self):
        return {
            "character": self.cid,
            "name": self.name,
            "attack_roll": 'Attack Roll' in self.types,
            "saving_throw": 'Saving Throw' in self.types,
            "attribute": self.attr,
            "target": self.target,
            "proficient": self.proficient,
            "modifiers": self.modifiers,
            "damage_roll": self.damage_roll
        }
    
    async def insert_attack(self, interaction):
        data = self.return_data()
        interaction.client.db.insert(
                "attacks",
                {"aid": 0, 
                 "cid": int(data['character']),
                 "name": data['name'],
                 "attack_roll": int(data['attack_roll']), 
                 "saving_throw": int(data['saving_throw']),
                 "attribute": data['attribute'],
                 "target": data['target'],
                 "proficient": int(data['proficient']),
                 "modifiers": data['modifiers'],
                 "damage_roll": data['damage_roll']}
            )

def setup(bot):
    """Called by Pycord to setup the cog"""
    cog = CogAttacks(bot)
    cog.guild_ids = [bot.guild_id]
    bot.add_cog(cog)
