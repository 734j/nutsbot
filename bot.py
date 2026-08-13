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
import asyncio
import sys
import aiosqlite

CWD_PATH = os.getcwd()
sys.path.insert(1, f"{CWD_PATH}/misc")

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(intents=intents, command_prefix="(")
tree = bot.tree

COMMIT = '__VERSION__'
TOKEN = '__YOUR_TOKEN__'
SYS_DATABASE_DIR_PATH = "__YOUR_DATABASE_PATH__"


@tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    print(f"Slash Command Error in /{interaction.command.name}: {error}")


async def sync_guilds():
    if not bot.guilds:
        return

    guilds_data = [
        (str(g.id), g.name, g.member_count or 0, str(g.owner_id))
        for g in bot.guilds
    ]

    sql = """
    INSERT INTO guilds (guild_id, guild_name, guild_size, owner_id)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET
        guild_name = excluded.guild_name,
        guild_size = excluded.guild_size,
        owner_id = excluded.owner_id;
    """

    await bot.db.executemany(sql, guilds_data)
    await bot.db.commit()
    print(f"Successfully synced {len(guilds_data)} guild(s) to database.")


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    print(f"Database Path: {SYS_DATABASE_DIR_PATH}")
    print(f"Current Path: {CWD_PATH}")
    print(f"On version: {COMMIT}")
    await sync_guilds()


@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"Bot joined a new server: {guild.name}")
    await sync_guilds()

    
@bot.event
async def on_guild_remove(guild: discord.Guild):
    await bot.db.execute(
        "UPDATE guilds SET bot_is_enabled = 0 WHERE guild_id = ?",
        (str(guild.id),)
    )
    await bot.db.commit()


@bot.event
async def on_message(message):
    if message.author == bot.user:  # bot doesn't reply to itself
        return

    if message.author.bot or not message.guild:
        return
    
    guild_id_str = str(message.guild.id)
    msg_content_lower = message.content.lower()

    sql = """
    SELECT trigger_phrase, response_phrase
    FROM reactions
    JOIN guilds ON guilds.guild_id = reactions.guild_id
    WHERE reactions.guild_id = ? AND guilds.bot_is_enabled = 1;
    """

    async with bot.db.execute(sql, (guild_id_str,)) as cursor:
        reactions = await cursor.fetchall()  # Returns list of tuples: [('nuts', '<:nuts:...>'), ...]


    for trigger_phrase, response_phrase in reactions:
        if trigger_phrase.lower() in msg_content_lower:
            await message.channel.send(response_phrase)
            break
    
    await bot.process_commands(message)


@tree.command(name="nuts", description="NUTS!")
async def _nuts(interaction: discord.Interaction):
    await interaction.response.send_message("<:nuts:1424932626023841893>")

@tree.command(name="add-reaction", description="Add a reaction. You can have 50 reactions in total.")
async def _add_reaction(interaction: discord.Interaction, trigger: str, response: str):
    if not interaction.guild_id:
        await interaction.response.send_message(
            "This command can only be used in a server!", ephemeral=True
        )
        return

    if not interaction.permissions.administrator:
        await interaction.response.send_message(
            "You need **Administrator** permissions to use this command!",
            ephemeral=True,
        )
        return
    
    guild_id = str(interaction.guild_id)

    async with bot.db.execute(
        "SELECT COUNT(*) FROM reactions WHERE guild_id = ?", (guild_id,)
    ) as cursor:
        row = await cursor.fetchone()
        current_count = row[0] if row else 0

    if current_count >= 50:
        await interaction.response.send_message(
            "Your server is limited to **50 reactions**!",
            ephemeral=True,
        )
        return
    
    sql = """
    INSERT INTO reactions (guild_id, trigger_phrase, response_phrase)
    VALUES (? , ? , ?);
    """

    try:
        await bot.db.execute(sql, (guild_id, trigger.lower(), response))
        await bot.db.commit()
        
        await interaction.response.send_message(
            f"**Trigger:** `{trigger.lower()}`\n"
            f"**Response:** {response}"
        )

    except aiosqlite.IntegrityError:
        # This triggers if UNIQUE(guild_id, trigger_phrase) is violated
        await interaction.response.send_message(
            f"A reaction for the trigger `{trigger.lower()}` already exists in this server.",
            ephemeral=True,
        )


@tree.command(name="version", description="bot version")
async def ver(interaction: discord.Interaction):
    await interaction.response.send_message(f"Version: {COMMIT}")


# Setup hook runs AFTER HTTP login (application_id is known) but BEFORE gateway connection
async def setup_hook():
    await tree.sync()
    print("Slash commands synced successfully.")

bot.setup_hook = setup_hook


async def main():
    async with aiosqlite.connect(SYS_DATABASE_DIR_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")

        # Attach database connection globally to `bot`
        bot.db = db

        # Start the bot cleanly
        async with bot:
            await bot.start(TOKEN)


asyncio.run(main())
