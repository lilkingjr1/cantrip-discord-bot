"""CogAttacks.py

Handles all attacks associated with player characters from the database.
Date: 05/12/2023
Authors: David Wolfe, Scott Fisher, Sinjin Serrano
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import discord
from discord.ext import commands

from cogs.CogCharacters import get_player_characters

from cogs.CogRoll import parse_roll
from cogs.CogRoll import roll_dice
from cogs.CogRoll import create_result_string

from math import floor

ATTRIBUTES = [
    'Strength',
    'Dexterity',
    'Constitution',
    'Intelligence',
    'Wisdom',
    'Charisma'
]

BASE_DC = 8
PROF_INIT_BONUS = 2
ABILITY_DEFAULT = 10
BULLET_EMOJI = ':small_blue_diamond:'

async def get_attacks(ctx: discord.AutocompleteContext):
    """Autocomplete Context: Get attacks
    
    Returns array of attacks names a character owns.
    """
    cids = ctx.bot.db.getAll(
        "characters", 
        ["cid"], 
        ("uid=%s", [ctx.interaction.user.id])
    )
    if cids:
        attacks = []
        for cid in cids:
            attacks.append(ctx.bot.db.getAll(
                "attacks",
                ["name"],
                ("cid=%s", [cid['cid']]))
        )
        if attacks:
            return [attack['name'] for attack in attacks[0]]
        else:
            return []
    else:
        return []

def calc_proficiency_bonus(char_level, modifiers=0):
    """Calculates a character's proficiency bonus based off their level.
    """
    if char_level < 1:
        return 0 + modifiers
    return floor((char_level - 1) / 4) + PROF_INIT_BONUS + modifiers

def calc_ability_modifier(ability_score, modifiers=0):
    """Calculates a character's ability modifier off their ability score.
    """
    return floor((ability_score - ABILITY_DEFAULT) / 2) + modifiers

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
    
    @attack.command(name = "delete", description="Delete a character's attack.")
    async def create(
        self,
        ctx,
        character: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(get_player_characters),
            description="Which character's attack are you deleting?",
            max_length=255,
            required=True
        ),
        name: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(get_attacks),
            description="Name of the attack you are deleting.",
            max_length=255,
            required=True
        )
    ):
        """Slash Command: /attack delete
        
        Delete's specified attack.
         - character: string of the attack's character (autocompleted)
         - name: string of the attack's name (autocompleted)
        """
        _cid = self.bot.db.getOne(
            "characters",
            ["cid"],
            ("uid=%s and name=%s", [ctx.author.id, character])
        )
        if _cid:
            self.bot.db.delete(
                "attacks",
                ("cid=%s and name=%s", [_cid['cid'], name])
            )
            await ctx.respond("Deleted {}'s {}!".format(character, name), ephemeral=True)
        else:
            await ctx.respond("Something went wrong.", ephemeral=True)
    
    @attack.command(name = "list", description="Displays a list of a character's attacks.")
    async def create(
        self,
        ctx,
        character: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(get_player_characters),
            description="Which character's attacks are you viewing?",
            max_length=255,
            required=True
        ),
    ):
        """Slash Command: /attack list
        
        Lists a character's attacks.
         - character: string of the character(autocompleted)
        """
        _cid = self.bot.db.getOne(
            "characters",
            ["cid"],
            ("uid=%s and name=%s", [ctx.author.id, character])
        )
        if _cid:
            _attacks = self.bot.db.getAll(
                "attacks",
                ["name"],
                ("cid=%s", [_cid['cid']])
            )
            if _attacks:
                output = "**{}'s attacks:**\n>>> ".format(character)
                _attacks_sorted = sorted(_attacks, key=lambda x: x['name'])
                for atk in _attacks_sorted:
                    output += BULLET_EMOJI + ' ' + atk['name'] + '\n'
                await ctx.respond(output, ephemeral=True)
            else:
                await ctx.respond("{} does not have any attacks!".format(character), ephemeral=True)
        else:
            await ctx.respond("Something went wrong.", ephemeral=True)

    @attack.command(name = "view", description="Displays a character's attack.")
    async def create(
        self,
        ctx,
        character: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(get_player_characters),
            description="Which character's attacks are you viewing?",
            max_length=255,
            required=True
        ),
        name: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(get_attacks),
            description="Which attack are you viewing?.",
            max_length=255,
            required=True
        ),
        public: discord.Option(
            bool,
            description="Make attack visible to everyone?",
            required=False
        )
    ):
        """Slash Command: /attack view
        
        Displays a character's attack.
         - character: string of the character(autocompleted)
         - name: string of the attack name
         - public: bool; if message is ephemeral or not (not required)
        """
        _cid = self.bot.db.getOne(
            "characters",
            ["cid", "portrait", "level", "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
            ("uid=%s and name=%s", [ctx.author.id, character])
        )
        if _cid:
            _attack = self.bot.db.getOne(
                "attacks",
                ["name", "attack_roll", "saving_throw", "attribute", "target", "proficient", "modifiers", "damage_roll"],
                ("cid=%s and name=%s", [_cid['cid'], name])
            )
            if _attack:
                # Create nice pretty embed
                embed = discord.Embed(
                    title =_attack['name'],
                    color = discord.Color.blurple()
                )

                embed.add_field(name='**Damage Roll**', value=_attack['damage_roll'])

                if _attack['attack_roll']:
                    ability_modifier = calc_ability_modifier(_cid[_attack['attribute'].lower()])
                    prof_bonus = calc_proficiency_bonus(_cid['level']) * _attack['proficient']
                    attack_bonus = _attack['modifiers']

                    total_bonus = ability_modifier + prof_bonus + attack_bonus

                    details = '-' if ability_modifier < 0 else '+'
                    details += "{:<2}, {:>24}\n".format(ability_modifier, '*' + _attack['attribute'] + ' modifier*')
                    if _attack['proficient']:
                        details += '+' if prof_bonus >= 0 else ''
                        details += "{:<2}, {:>24}\n".format(prof_bonus, '*proficiency bonus*')
                    if attack_bonus != 0:
                        details += '+' if attack_bonus >= 0 else ''
                        details += "{:<2}, {:>24}\n".format(attack_bonus, '*innate modifiers*')

                    embed.add_field(name="**Attack Roll ({}) Bonus: {}**".format(_attack['attribute'], total_bonus), value=details)
                if _attack['saving_throw']:
                    ability_modifier = calc_ability_modifier(_cid[_attack['attribute'].lower()])
                    prof_bonus = calc_proficiency_bonus(_cid['level']) * _attack['proficient']
                    attack_bonus = _attack['modifiers']

                    save_dc = ability_modifier + prof_bonus + attack_bonus + BASE_DC

                    details = '-' if ability_modifier < 0 else '+'
                    details += "{:<2}, {:>24}\n".format(ability_modifier, '*' + _attack['attribute'] + ' modifier*')
                    if _attack['proficient']:
                        details += '-' if prof_bonus < 0 else '+'
                        details += "{:<2}, {:>24}\n".format(prof_bonus, '*proficiency bonus*')
                    if attack_bonus != 0:
                        details += '-' if attack_bonus < 0 else '+'
                        details += "{:<2}, {:>24}\n".format(attack_bonus, '*innate modifiers*')
                    
                    embed.add_field(name="**Save DC ({}): {}**".format(_attack['target'], save_dc), value=details)

                # Extra info
                embed.set_author(name='{}'.format(character), icon_url=(_cid['portrait']))

                await ctx.respond(embed=embed, ephemeral=(public is not True))
            else:
                await ctx.respond("Attack not found.")
        else:
            await ctx.respond("Something went wrong.")

    @attack.command(name = "roll", description="Displays a character's attack.")
    async def create(
        self,
        ctx,
        character: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(get_player_characters),
            description="Which character's attacks are you viewing?",
            max_length=255,
            required=True
        ),
        name: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(get_attacks),
            description="Which attack are you viewing?.",
            max_length=255,
            required=True
        )
    ):
        """Slash Command: /attack roll
        
        Rolls a character's attack.
         - character: string of the character(autocompleted)
         - name: string of the attack name
        """
        _cid = self.bot.db.getOne(
            "characters",
            ["cid", "portrait", "level", "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
            ("uid=%s and name=%s", [ctx.author.id, character])
        )
        if _cid:
            _attack = self.bot.db.getOne(
                "attacks",
                ["name", "attack_roll", "saving_throw", "attribute", "target", "proficient", "modifiers", "damage_roll"],
                ("cid=%s and name=%s", [_cid['cid'], name])
            )
            if _attack:
                init_content = "{} uses {}!".format(character, name)
                await ctx.respond(
                init_content,
                view=AttackConfirmView(_cid, _attack, init_content)
            )
            else:
                await ctx.respond("Attack not found.")
        else:
            await ctx.respond("Something went wrong.")

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
            self.add_item(discord.ui.InputText(label="ATTACK ROLL MODIFIERS / SAVE DC MODIFIERS"))
        self.add_item(discord.ui.InputText(label="DAMAGE ROLL"))


class AttackView(discord.ui.View):
    """View for the attack creation user interface.
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
            AttrButton(label=attr, style=discord.ButtonStyle.primary, custom_id=(attr + '_target'),
            row=floor(ATTRIBUTES.index(attr) / 3) + 2)
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
            await interaction.response.edit_message(content="**Select the attack's attribute. (Ability modifier added to attack roll.)**", view=self)
        else:
            self.prompt_is_proficient()
            await interaction.response.edit_message(content="**Are you proficient in this attack?**", view=self)
        

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
            await interaction.response.edit_message(content="**Select attribute of saving throw.**", view=self)
        else:
            self.prompt_is_proficient()
            await interaction.response.edit_message(content="**Are you proficient in this attack?**", view=self)
        
    
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

class AttackConfirmView(discord.ui.View):
    """View for confirming if an attack roll hits and/or a saving throw is failed.
    """
    def __init__(self, character, attack, init_content='placeholder'):
        super().__init__()
        self._character = character # dictionary of character DB entry
        self._attack = attack # dictionary of attack DB entry
        self._roll_button = AttrButton(label='Roll attack!', style=discord.ButtonStyle.primary, custom_id='Attack')
        self._attack_buttons = [
            AttrButton(label='Yes', style=discord.ButtonStyle.primary, custom_id='aYes'),
            AttrButton(label='No', style=discord.ButtonStyle.primary, custom_id='aNo')
        ]
        self._save_buttons = [
            AttrButton(label='Yes', style=discord.ButtonStyle.primary, custom_id='Yes'),
            AttrButton(label='No', style=discord.ButtonStyle.primary, custom_id='No')
        ]
        self._hit = False
        self._failed = False
        self._content = init_content
        self.prompt_roll()
        
    
    async def roll_prompt_callback(self, interaction):
        self.remove_item(self._roll_button)
        if self._attack['attack_roll']:
            self.prompt_attack_hit()
            await self.show_attack(interaction)
            
        elif self._attack['saving_throw']:
            self.prompt_save_failed()
            await self.show_save(interaction)
            
        else:
            await self.roll_damage(interaction)

    async def show_attack(self, interaction):
        ability_modifier = calc_ability_modifier(self._character[self._attack['attribute'].lower()])
        prof_bonus = calc_proficiency_bonus(self._character['level']) * self._attack['proficient']
        attack_bonus = self._attack['modifiers']
        total_bonus = ability_modifier + prof_bonus + attack_bonus
        rolls, total = roll_dice(1, 20, total_bonus)
        total_bonus_str = '+' if total_bonus >= 0 else ''
        total_bonus_str += str(total_bonus)
        msg = create_result_string(rolls, total, 1, 20, total_bonus, total_bonus_str)
        
        msg += "\nDoes your attack hit?"
        self._content += '\n' + msg
        await interaction.response.edit_message(content=self._content, view=self)
    
    async def show_save(self, interaction):
        ability_modifier = calc_ability_modifier(self._character[self._attack['attribute'].lower()])
        prof_bonus = calc_proficiency_bonus(self._character['level']) * self._attack['proficient']
        attack_bonus = self._attack['modifiers']
        total_bonus = ability_modifier + prof_bonus + attack_bonus + BASE_DC
        msg = "Did your target fail their saving throw? (**{} Save DC: {}**)".format(self._attack['target'], total_bonus)
        self._content += '\n' + msg
        await interaction.response.edit_message(content=self._content, view=self)

    async def attack_hit_callback(self, interaction):
        self._hit = interaction.custom_id == 'aYes'
        # Disable all Yes/No buttons
        for b in self._attack_buttons:
            if 'a' + b.label == interaction.custom_id:
                b.style = discord.ButtonStyle.success
            b.disabled = True
            self.remove_item(b)
        if self._attack['saving_throw'] and self._hit:
            self.prompt_save_failed()
            await self.show_save(interaction)
        elif self._hit:
            await self.roll_damage(interaction)
        else:
            await self.failed_attack(interaction)
    
    async def save_failed_callback(self, interaction):
        self._failed = interaction.custom_id == 'Yes'
        # Disable all Yes/No buttons
        for b in self._save_buttons:
            if b.label == interaction.custom_id:
                b.style = discord.ButtonStyle.success
            b.disabled = True
            self.remove_item(b)
        if self._failed:
            await self.roll_damage(interaction)
        else:
            await self.failed_attack(interaction)

    def prompt_roll(self):
        self._roll_button.callback = self.roll_prompt_callback
        self.add_item(self._roll_button)

    def prompt_attack_hit(self):
        for b in self._attack_buttons:
            b.callback = self.attack_hit_callback
            self.add_item(b)
    
    def prompt_save_failed(self):
        for b in self._save_buttons:
            b.callback = self.save_failed_callback
            self.add_item(b)
    
    async def roll_damage(self, interaction):
        results = parse_roll([self._attack['damage_roll']])
        self._content += '\n' + results[0]
        await interaction.response.edit_message(content=self._content, view=self)
    
    async def failed_attack(self, interaction):
        self._content += '\n' + 'D:' # TODO: add document of random failure text
        await interaction.response.edit_message(content=self._content, view=self)


def setup(bot):
    """Called by Pycord to setup the cog"""
    cog = CogAttacks(bot)
    cog.guild_ids = [bot.guild_id]
    bot.add_cog(cog)
