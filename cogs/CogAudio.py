"""CogAudio.py

Handles all commands associated with playing local background ambiance audio.
Date: 05/12/2023
Authors: David Wolfe
Licensed under GNU GPLv3 - See LICENSE for more details.
"""

import os
import shutil
import asyncio

import discord
from discord.ext import commands


AUDIO_DIR = './audio/'
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg']
CMD_COOLDOWN = 1 # Seconds


async def get_local_audio(ctx: discord.AutocompleteContext):
    """Autocomplete Context: Get local audio files
    
    Returns array of all audio files currently in the `audio/` directory.
    """
    return [f for f in os.listdir(AUDIO_DIR) if os.path.splitext(f)[1] in AUDIO_EXTENSIONS]


class CogAudio(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ffmpeg_loaded = False
        self.repeat_on = False
        self.cur_volume = 1.0
    

    @commands.Cog.listener()
    async def on_ready(self):
        """Listener: On Cog Ready
        
        Runs when the cog is successfully cached within the Discord API.
        """
        if shutil.which('ffmpeg') is not None:
            self.ffmpeg_loaded = True
            print(f"{self.bot.get_datetime_str()}: [Audio] Successfully cached!")
        else:
            print("WARNING: [Audio] Disabled because 'ffmpeg' is either not installed or is not in system PATH!")
    
    
    """Slash Command Group: /audio
    
    A group of commands related to managing the playing of audio.
    """
    audio = discord.SlashCommandGroup(
        "audio", 
        "Commands to play background ambiance audio loaded on the bot"
    )


    @audio.command(name = "play", description="Plays background ambiance audio loaded on the bot")
    @commands.cooldown(1, CMD_COOLDOWN, commands.BucketType.member)
    async def play(
        self, 
        ctx, 
        file: discord.Option(
            str, 
            description="Name of audio file to play", 
            autocomplete=discord.utils.basic_autocomplete(get_local_audio), 
            required=True
        )
    ):
        """Slash Command: /audio play
        
        Plays a local audio file.
        """
        # Sanitize input
        if file in await get_local_audio(ctx):
            await ctx.respond(f'Now playing: "{file}"')
            # While loop is to support repeat function -- this is ugly, don't look at it
            while True:
                # Loads FFmpeg handle of audio file
                source = discord.FFmpegPCMAudio(AUDIO_DIR + file)
                # Transforms an audio source to have volume controls.
                source = discord.PCMVolumeTransformer(source, volume=self.cur_volume)
                # Play the audio file
                ctx.voice_client.play(
                    source, after=lambda e: print(f"Player error: {e}") if e else None
                )
                # Wait for the audio to finish playing
                while ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                    await asyncio.sleep(1)
                # Check for repeat
                if not self.repeat_on or not ctx.voice_client: break
            # Disconnect from the voice channel
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
        else:
            await ctx.voice_client.disconnect()
            raise commands.CommandError(f'"{file}" is not an audio file that is loaded on the bot.')

    @audio.command(name = "stop", description="Stops Cantrip from playing audio and disconnects it")
    async def stop(self, ctx):
        """Slash Command: /audio stop
        
        Stops playing audio and disconnects the bot from voice.
        """
        _response = await ctx.respond("Stopping...", ephemeral=True)
        await ctx.voice_client.disconnect(force=True)
        await _response.delete_original_response()

    @audio.command(name = "pause", description="Pauses playing audio")
    async def pause(self, ctx):
        """Slash Command: /audio pause
        
        Pauses the audio player.
        """
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            return await ctx.respond("Cantrip is not currently playing any audio.", ephemeral=True)
        
        
        _response = await ctx.respond("Pausing...", ephemeral=True)
        ctx.voice_client.pause()
        await _response.delete_original_response()

    @audio.command(name = "resume", description="Resumes playing audio")
    async def resume(self, ctx):
        """Slash Command: /audio resume
        
        Resumes the audio player.
        """
        if ctx.voice_client is None:
            return await ctx.respond("Use `/audio play` to choose a song to play.", ephemeral=True)
        
        _response = await ctx.respond("Resuming...", ephemeral=True)
        if not ctx.voice_client.is_playing():
            ctx.voice_client.resume()
        await _response.delete_original_response()
    
    @audio.command(name = "volume", description="Changes the volume of playing audio")
    async def volume(
        self, 
        ctx, 
        percent: discord.Option(
            int, 
            description="New volume percentage", 
            min_value=1, 
            max_value=100, 
            required=True
        )
    ):
        """Slash Command: /audio volume
        
        Changes the player's volume.
        """
        self.cur_volume = percent / 100
        if ctx.voice_client is not None:
            ctx.voice_client.source.volume = self.cur_volume
        await ctx.respond(f"Changed volume to {percent}%", ephemeral=True)

    @audio.command(name = "repeat", description="Turn audio repeat on or off")
    async def repeat(
        self, 
        ctx, 
        setting: discord.Option(
            str, 
            choices=["On", "Off"], 
            required=True
        )
    ):
        """Slash Command: /audio repeat
        
        Sets if the audio player should repeat audio when it finishes.
        """
        if setting == "On":
            self.repeat_on = True
        else:
            self.repeat_on = False
        
        await ctx.respond(f"Turned repeat {setting}.", ephemeral=True)
    

    @play.before_invoke
    async def ensure_voice(self, ctx):
        """Before Invoke: Ensure Voice
        
        Checks if FFmpeg is installed.
        Prepares the bot to play new audio.
        Connects the bot to the author's voice channel.
        If it's already connected, it will stop the previous audio before playing the new audio.
        Presents an error if the author is not connected to a voice channel.
        """
        if not self.ffmpeg_loaded:
            raise commands.CommandError(":warning: Unable to run command at this time")
        
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                raise commands.CommandError("You must connect to a voice channel before Cantrip can play audio for you.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(bot):
    """Called by Pycord to setup the cog"""
    cog = CogAudio(bot)
    cog.guild_ids = [bot.guild_id]
    bot.add_cog(cog)
