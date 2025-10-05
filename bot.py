from discord import app_commands
from discord.utils import get  # New import
from discord.ext import commands
from random import randint
import os
import discord
import random
import time
from typing import Literal
from discord import AllowedMentions

from io import StringIO
import sys

CWD_PATH = (
    os.getcwd()
)  # This grabs the current working directory, no need for hardcoded strings.
sys.path.insert(1, f"{CWD_PATH}/misc")
import cowfiles


intents = discord.Intents.all()
intents.members = True
COMMIT = '__VERSION__'
TOKEN = '__YOUR_TOKEN__'
SYS_DATABASE_DIR_PATH = "__YOUR_DATABASE_PATH__"
#SYS_BADWORDS_DIR_PATH = "__YOUR_BAD_WORDS_PATH__"
bot = commands.Bot(command_prefix="(", intents=intents)
tree = bot.tree

# Guild ID
server_id = 938728183203758080

# Channels
channel_joinleave = 943602154428571708  # join and leave channel
channel_pplofthepit = 1243174332293976095
channel_pit = 1057343199888285786
channel_announcments = 1263195223803035668
channel_senate = 1241499601450827897
channel_blockedmessages = 1105231511512424508

# Roles
role_admin = 938787942657327114
role_mod = 977248936148500550
role_owner = 938732039207809025
role_bot_smileyface = 938795313815240734
role_bot2 = 998594848582025269
role_pitted = 1057342828205846538
role_member = 938804320026099742
role_swagballer = 1003732468370776125
role_anyone = 1263879103803687046
role_senator = 1376258876944551996
role_newgen = 1323689803035840585


@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=server_id))
    print("The bot has successfully started.")
    print(SYS_PIT_DIR_PATH)
    print(CWD_PATH)
    print(f"On version: {COMMIT}")


# @anyone
@bot.event
async def on_message(message):

    if message.author == bot.user:  # bot doesn't reply to itself
        return

    for role in message.role_mentions:
        if role_anyone == role.id:  # checks if @anyone pinged
            for anyoneMemb in role.members:
                await anyoneMemb.remove_roles(
                    discord.Object(id=role_anyone)
                )  # removes @anyone from previous owner

            guild = bot.get_guild(server_id)
            anyoneRand = random.choice(guild.members)
            await anyoneRand.add_roles(
                discord.Object(id=role_anyone)
            )  # adds @anyone to new owner

    if message.content.lower() == "give me admin":
        await generic_pit(discord.Interaction, message.author)
    return


@tree.command(name="hello", description="Hello nutsbot!", guild=discord.Object(id=server_id))
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")


@tree.command(name="bye", description="baii", guild=discord.Object(id=server_id))
async def bye(interaction: discord.Interaction):
    await interaction.response.send_message("Bye!")


@tree.command(
    name="version", description="bot version", guild=discord.Object(id=server_id)
)
async def ver(interaction: discord.Interaction):
    await interaction.response.send_message(f"Version: {COMMIT}")
    


bot.run(TOKEN)
