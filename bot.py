
import os
import asyncio
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from erlc_api import AsyncClient


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
ERLC_SERVER_KEY = os.getenv("ERLC_SERVER_KEY", "").strip()

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")

if not ERLC_SERVER_KEY:
    raise RuntimeError("ERLC_SERVER_KEY is missing from .env")


# ============================================================
# DISCORD SETUP
# ============================================================

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# STORAGE
# ============================================================

# Temporary warning storage.
# Warnings reset when the bot restarts.
warnings = {}


# ============================================================
# ER:LC API
# ============================================================

erlc = AsyncClient(server_key=ERLC_SERVER_KEY)


async def run_erlc_command(command: str):
    """Send a command to the ER:LC server."""
    try:
        result = await erlc.command(command)
        return result
    except Exception as e:
        print(f"ERLC API ERROR: {e}")
        raise


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print("Bot is online!")


# ============================================================
# PERMISSION CHECK
# ============================================================

def staff_only():
    """Slash command permission check for Discord staff."""
    async def predicate(interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ You need the **Manage Server** permission to use this command.",
                ephemeral=True
            )
            return False

        return True

    return app_commands.check(predicate)


# ============================================================
# /PING
# ============================================================

@bot.tree.command(
    name="ping",
    description="Check if the bot is online."
)
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)

    await interaction.response.send_message(
        f"🏓 Pong! `{latency}ms`"
    )


# ============================================================
# /SERVER
# ============================================================

@bot.tree.command(
    name="server",
    description="Show ER:LC server information."
)
async def server(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        info = await erlc.server()

        embed = discord.Embed(
            title="🚓 ER:LC Server",
            description=f"**{info.name}**",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Players",
            value=f"{info.current_players}/{info.max_players}",
            inline=True
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(
            f"❌ Could not get server information.\n`{e}`"
        )


# ============================================================
# /PLAYERS
# ============================================================

@bot.tree.command(
    name="players",
    description="Show players currently in the ER:LC server."
)
async def players(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        player_list = await erlc.players()

        if not player_list:
            await interaction.followup.send(
                "👥 There are currently no players in the server."
            )
            return

        lines = []

        for player in player_list:
            name = getattr(player, "name", "Unknown")
            team = getattr(player, "team", "Unknown")
            lines.append(f"• **{name}** — {team}")

        embed = discord.Embed(
            title=f"👥 ER:LC Players ({len(player_list)})",
            description="\n".join(lines[:50]),
            color=discord.Color.green()
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(
            f"❌ Could not get players.\n`{e}`"
        )


# ============================================================
# /ANNOUNCE
# ============================================================

@bot.tree.command(
    name="announce",
    description="Send an announcement to the ER:LC server."
)
@app_commands.describe(message="The message to announce")
@app_commands.checks.has_permissions(manage_guild=True)
async def announce(
    interaction: discord.Interaction,
    message: str
):
    await interaction.response.defer(ephemeral=True)

    if len(message) > 120:
        await interaction.followup.send(
            "❌ Your announcement is too long. Keep it under 120 characters.",
            ephemeral=True
        )
        return

    try:
        await run_erlc_command(f":h {message}")

        await interaction.followup.send(
            "✅ Announcement sent to the ER:LC server.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to send announcement.\n`{e}`",
            ephemeral=True
        )


# ============================================================
# /COMMAND
# ============================================================

@bot.tree.command(
    name="command",
    description="Run an ER:LC server command."
)
@app_commands.describe(command="The ER:LC command, for example :h Hello")
@app_commands.checks.has_permissions(administrator=True)
async def command(
    interaction: discord.Interaction,
    command: str
):
    await interaction.response.defer(ephemeral=True)

    if len(command) > 120:
        await interaction.followup.send(
            "❌ Command is too long. Maximum 120 characters.",
            ephemeral=True
        )
        return

    if not command.startswith(":"):
        await interaction.followup.send(
            "❌ ER:LC commands must start with `:`.\nExample: `:h Hello`",
            ephemeral=True
        )
        return

    try:
        result = await run_erlc_command(command)

        message = getattr(result, "message", "Command sent.")

        await interaction.followup.send(
            f"✅ Command executed.\n`{message}`",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to execute command.\n`{e}`",
            ephemeral=True
        )


# ============================================================
# ER:LC PLAYER MANAGEMENT
# ============================================================

@bot.tree.command(
    name="kickplayer",
    description="Kick a player from the ER:LC server."
)
@app_commands.describe(player="The exact ER:LC player username")
@app_commands.checks.has_permissions(kick_members=True)
async def kickplayer(
    interaction: discord.Interaction,
    player: str
):
    await interaction.response.defer(ephemeral=True)

    try:
        await run_erlc_command(f":kick {player}")

        await interaction.followup.send(
            f"✅ **{player}** was kicked from the ER:LC server.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to kick player.\n`{e}`",
            ephemeral=True
        )


@bot.tree.command(
    name="banplayer",
    description="Ban a player from the ER:LC server."
)
@app_commands.describe(player="The exact ER:LC player username")
@app_commands.checks.has_permissions(ban_members=True)
async def banplayer(
    interaction: discord.Interaction,
    player: str
):
    await interaction.response.defer(ephemeral=True)

    try:
        await run_erlc_command(f":ban {player}")

        await interaction.followup.send(
            f"🔨 **{player}** was banned from the ER:LC server.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to ban player.\n`{e}`",
            ephemeral=True
        )


@bot.tree.command(
    name="unbanplayer",
    description="Unban a player from the ER:LC server."
)
@app_commands.describe(player="The exact ER:LC player username")
@app_commands.checks.has_permissions(ban_members=True)
async def unbanplayer(
    interaction: discord.Interaction,
    player: str
):
    await interaction.response.defer(ephemeral=True)

    try:
        await run_erlc_command(f":unban {player}")

        await interaction.followup.send(
            f"✅ **{player}** was unbanned from the ER:LC server.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to unban player.\n`{e}`",
            ephemeral=True
        )


# ============================================================
# DISCORD BAN
# ============================================================

@bot.tree.command(
    name="ban",
    description="Ban a Discord member."
)
@app_commands.describe(
    member="The member to ban",
    reason="Reason for the ban"
)
@app_commands.checks.has_permissions(ban_members=True)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):
    if member == interaction.user:
        await interaction.response.send_message(
            "❌ You cannot ban yourself.",
            ephemeral=True
        )
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message(
            "❌ You cannot ban someone with an equal or higher role.",
            ephemeral=True
        )
        return

    try:
        await member.ban(reason=reason)

        await interaction.response.send_message(
            f"🔨 **{member}** has been banned.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to ban that member.",
            ephemeral=True
        )


# ============================================================
# DISCORD UNBAN
# ============================================================

@bot.tree.command(
    name="unban",
    description="Unban a Discord user using their ID."
)
@app_commands.describe(user_id="The Discord user ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(
    interaction: discord.Interaction,
    user_id: str
):
    try:
        user = await bot.fetch_user(int(user_id))

        await interaction.guild.unban(user)

        await interaction.response.send_message(
            f"✅ **{user}** has been unbanned."
        )

    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid user ID.",
            ephemeral=True
        )

    except discord.NotFound:

