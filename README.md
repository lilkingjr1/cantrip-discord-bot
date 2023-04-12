![Cantrip - *An All-Purpose D&D Discord Bot*](logo.jpg)

[![Bitbucket release (latest by date)](https://img.shields.io/badge/release-0.0.0-blue?logo=bitbucket)](https://bitbucket.org/comp-350-2/cantrip-discord-bot/src/master/) [![Python version](https://img.shields.io/badge/python-3.x.x-brightgreen?logo=python)](https://www.python.org/downloads/) ![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux-lightgrey) ![Hosting](https://img.shields.io/badge/hosting-self--hosted-blue) [![License](https://img.shields.io/badge/license-GNU%20GPLv3-green)](https://bitbucket.org/comp-350-2/cantrip-discord-bot/src/master/LICENSE)

___

Cantrip is a self-hosted Discord bot, written in Python using the Pycord API, with the goal of making the
popular tabletop game "Dungeons and Dragons 5th Edition" (D&D 5e) easier to organize and
play by providing a suite of organizational and planning tools. With the helpful tools Cantrip
provides, new and experienced players alike will find playing via Discord to be easier than ever
before.

___

## Prerequisites

- Python 3
- PIP (should be included with Python)
- Discord account with verified email (to access developer portal)

## Installation

### Creating a Discord Application for the Bot

1. Go to Discord's [Developer Portal](http://discordapp.com/developers/applications) and log in.
2. Click "New Application"
3. Name it "Cantrip" (or honestly whatever you'd like).
4. (Optional) Feel free to give it an App Icon (`icon.jpg` can be used) and Description of whatever you'd like. Click "Save Changes".
5. Click the "Bot" tab on the left and click "Add Bot". Then click "Yes, do it!".
6. Scroll down and turn on "SERVER MEMBERS INTENT" and "MESSAGE CONTENT INTENT". Click "Save Changes".
7. Click the "OAuth2" tab on the left and click "URL Generator".
8. Check these Scopes:

![scopes](https://user-images.githubusercontent.com/4533989/215032768-fb2c4887-85cd-42fe-adaf-5927f17cb2a6.jpg)

9. Check these Bot Permissions:

![bot_permissions #TODO - Will need to be updated as development continues](https://user-images.githubusercontent.com/4533989/215032794-58778138-6889-4996-9965-4ecca7cf9ddb.jpg)

10. Copy the Generated URL, paste it into a new tab, and invite the bot to the Discord server of your choosing.

### Installing the Bot

1. [Download the latest release](https://bitbucket.org/comp-350-2/cantrip-discord-bot/downloads/) and extract it (or `git clone` this repo), and place it wherever you'd like on the host.
2. Rename `.env-sample` to `.env`
3. Open command prompt or a terminal and navigate to the bot's folder:

```bash
cd /your/path/to/Cantrip-Discord-Bot
```

4. Verify you have the right version of Python installed:

```bash
python --version
OR (depending on what's in your PATH)
python3 --version
```
5. Install dependancies:
```bash
pip install -r requirements.txt
```

### Configure the Bot

The `.env` file can be used to configure the bot, or standard OS environment variables can be used (if so, reference the `.env` file for variable names).
1. Open `.env` with a text editor of your choice.
2. Set the Discord Token
    - Go to the Discord Developer Portal mentioned above
    - Go to the Bot tab
    - Click "Reset Token"
    - Copy the token
    - Replace `YOUR_DISCORD_TOKEN_HERE` with your token
3. Set the various Discord IDs
    - Open the Discord app
    - Click on the settings cog in the bottom left corner
    - Go to the Advanced tab and turn on "Developer Mode"
    - Right click the Channel/User you need the ID for, and click "Copy ID"
4. Set other settings according to their descriptions.
5. Save the file.

## Startup

Start with:
```bash
python bot.py
OR (depending on what's in your PATH)
python3 bot.py
```

## Usage & Commands

#TODO - Can be expanded on

| Command | Description |
|---------|-------------|
| `/about` | Displays information about the bot. |
| `/shutdown` | Cleanly shuts down the bot (only members with the Administrator permission can do this). |

The bot also responds positively to "good bot" remarks 🙂
