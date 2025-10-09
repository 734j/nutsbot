from discord import app_commands
from discord.utils import get
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
import sqlite3

CWD_PATH = (
    os.getcwd()
)

sys.path.insert(1, f"{CWD_PATH}/misc")


intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(intents=intents, command_prefix="(")
tree = bot.tree


COMMIT = '__VERSION__'
TOKEN = '__YOUR_TOKEN__'
SYS_DATABASE_DIR_PATH = "__YOUR_DATABASE_PATH__"


@bot.event
async def on_ready():
    await tree.sync()
    print("The bot has successfully started.")
    print(SYS_DATABASE_DIR_PATH)
    print(CWD_PATH)
    print(f"On version: {COMMIT}")
    with open("guilds.txt", "w", encoding="utf-8") as file:
        for guild in bot.guilds:
            line = f"\n{guild.name} (ID: {guild.id})\nMember Count: {guild.member_count}\n"
            file.write(line)
            print(f"Wrote to file: {line.strip()}")


@bot.event
async def on_message(message):

    if message.author == bot.user:  # bot doesn't reply to itself
        return


    if "nuts" in message.content.lower():
        await message.channel.send('<:nuts:1424932626023841893>')
    return


@tree.command(
    name="nuts", description="NUTS!"
)
async def _nuts(interaction: discord.Interaction):
    await interaction.response.send_message(f"<:nuts:1424932626023841893>")

@tree.command(
    name="version", description="bot version"
)
async def ver(interaction: discord.Interaction):
    await interaction.response.send_message(f"Version: {COMMIT}")
    


bot.run(TOKEN)
