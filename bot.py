

import os
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from erlc_api import AsyncClient


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
ERLC_SERVER_KEY = os.getenv("ERLC_SERVER_KEY", "").strip()

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")

if not ERLC_SERVER_KEY:
    raise RuntimeError("ERLC_SERVER_KEY is missing from .env")


# ============================================================
# DISCORD BOT
# ============================================================

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# ER:LC API
# ============================================================

erlc = AsyncClient(server_key=ERLC_SERVER_KEY)


async def erlc_command(command: str):
    try:
        return await erlc.command(command)
    except Exception as e:
        print(f"ERLC API ERROR: {e}")
        raise


# ============================================================
# WARNING STORAGE
# ============================================================

warnings = {}


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
        print(f"Command sync error: {e}")

    print("Bot is online!")


# ============================================================
# PING
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
# ER:LC SERVER
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
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Server",
            value=str(getattr(info, "name", "Unknown")),
            inline=False
        )

        embed.add_field(
            name="Players",
            value=f"{getattr(info, 'current_players', '?')}/"
                  f"{getattr(info, 'max_players', '?')}",
            inline=True
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:

        await interaction.followup.send(
            f"❌ Could not get ER:LC server information.\n"
            f"`{e}`"
        )


# ============================================================
# ER:LC PLAYERS
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
                "👥 There are currently no players in the ER:LC server."
            )
            return

        lines = []

        for player in player_list:

            name = getattr(player, "name", "Unknown")
            team = getattr(player, "team", "Unknown")

            lines.append(
                f"• **{name}** — {team}"
            )

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
# ANNOUNCE
# ============================================================

@bot.tree.command(
    name="announce",
    description="Send an announcement to the ER:LC server."
)
@app_commands.describe(
    message="Message to announce"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def announce(
    interaction: discord.Interaction,
    message: str
):

    await interaction.response.defer(
        ephemeral=True
    )

    try:

        await erlc_command(
            f":h {message}"
        )

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
# ER:LC COMMAND
# ============================================================

@bot.tree.command(
    name="command",
    description="Run an ER:LC server command."
)
@app_commands.describe(
    command="Example: :h Hello"
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def command(
    interaction: discord.Interaction,
    command: str
):

    await interaction.response.defer(
        ephemeral=True
    )

    if not command.startswith(":"):

        await interaction.followup.send(
            "❌ ER:LC commands must start with `:`.\n"
            "Example: `/command :h Hello`",
            ephemeral=True
        )
        return

    try:

        result = await erlc_command(command)

        await interaction.followup.send(
            f"✅ ER:LC command sent.\n`{result}`",
            ephemeral=True
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Failed to execute command.\n`{e}`",
            ephemeral=True
        )


# ============================================================
# ER:LC KICK PLAYER
# ============================================================

@bot.tree.command(
    name="kickplayer",
    description="Kick a player from the ER:LC server."
)
@app_commands.describe(
    player="Exact ER:LC player username"
)
@app_commands.checks.has_permissions(
    kick_members=True
)
async def kickplayer(
    interaction: discord.Interaction,
    player: str
):

    await interaction.response.defer(
        ephemeral=True
    )

    try:

        await erlc_command(
            f":kick {player}"
        )

        await interaction.followup.send(
            f"👢 **{player}** was kicked from ER:LC.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Failed to kick player.\n`{e}`",
            ephemeral=True
        )


# ============================================================
# ER:LC BAN PLAYER
# ============================================================

@bot.tree.command(
    name="banplayer",
    description="Ban a player from the ER:LC server."
)
@app_commands.describe(
    player="Exact ER:LC player username"
)
@app_commands.checks.has_permissions(
    ban_members=True
)
async def banplayer(
    interaction: discord.Interaction,
    player: str
):

    await interaction.response.defer(
        ephemeral=True
    )

    try:

        await erlc_command(
            f":ban {player}"
        )

        await interaction.followup.send(
            f"🔨 **{player}** was banned from ER:LC.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Failed to ban player.\n`{e}`",
            ephemeral=True
        )


# ============================================================
# ER:LC UNBAN PLAYER
# ============================================================

@bot.tree.command(
    name="unbanplayer",
    description="Unban a player from the ER:LC server."
)
@app_commands.describe(
    player="Exact ER:LC player username"
)
@app_commands.checks.has_permissions(
    ban_members=True
)
async def unbanplayer(
    interaction: discord.Interaction,
    player: str
):

    await interaction.response.defer(
        ephemeral=True
    )

    try:

        await erlc_command(
            f":unban {player}"
        )

        await interaction.followup.send(
            f"✅ **{player}** was unbanned from ER:LC.",
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
    member="Member to ban",
    reason="Reason for the ban"
)
@app_commands.checks.has_permissions(
    ban_members=True
)
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

        await member.ban(
            reason=reason
        )

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
    description="Unban a Discord user."
)
@app_commands.describe(
    user_id="Discord user ID"
)
@app_commands.checks.has_permissions(
    ban_members=True
)
async def unban(
    interaction: discord.Interaction,
    user_id: str
):

    try:

        user = await bot.fetch_user(
            int(user_id)
        )

        await interaction.guild.unban(
            user
        )

        await interaction.response.send_message(
            f"✅ **{user}** has been unbanned."
        )

    except ValueError:

        await interaction.response.send_message(
            "❌ Invalid Discord user ID.",
            ephemeral=True
        )

    except discord.NotFound:

        await interaction.response.send_message(
            "❌ That user is not banned.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to unban users.",
            ephemeral=True
        )


# ============================================================
# DISCORD KICK
# ============================================================

@bot.tree.command(
    name="kick",
    description="Kick a Discord member."
)
@app_commands.describe(
    member="Member to kick",
    reason="Reason for the kick"
)
@app_commands.checks.has_permissions(
    kick_members=True
)
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if member == interaction.user:

        await interaction.response.send_message(
            "❌ You cannot kick yourself.",
            ephemeral=True
        )
        return

    if member.top_role >= interaction.user.top_role:

        await interaction.response.send_message(
            "❌ You cannot kick someone with an equal or higher role.",
            ephemeral=True
        )
        return

    try:

        await member.kick(
            reason=reason
        )

        await interaction.response.send_message(
            f"👢 **{member}** has been kicked.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to kick that member.",
            ephemeral=True
        )


# ============================================================
# TIMEOUT
# ============================================================

@bot.tree.command(
    name="timeout",
    description="Timeout a Discord member."
)
@app_commands.describe(
    member="Member to timeout",
    minutes="Duration in minutes",
    reason="Reason for timeout"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def timeout(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: app_commands.Range[int, 1, 40320],
    reason: str = "No reason provided"
):

    if member == interaction.user:

        await interaction.response.send_message(
            "❌ You cannot timeout yourself.",
            ephemeral=True
        )
        return

    if member.top_role >= interaction.user.top_role:

        await interaction.response.send_message(
            "❌ You cannot timeout someone with an equal or higher role.",
            ephemeral=True
        )
        return

    try:

        await member.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏱️ **{member}** has been timed out for "
            f"**{minutes} minutes**.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to timeout that member.",
            ephemeral=True
        )


# ============================================================
# REMOVE TIMEOUT
# ============================================================

@bot.tree.command(
    name="untimeout",
    description="Remove a member's timeout."
)
@app_commands.describe(
    member="Member to untimeout"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def untimeout(
    interaction: discord.Interaction,
    member: discord.Member
):

    try:

        await member.timeout(None)

        await interaction.response.send_message(
            f"✅ Timeout removed from **{member}**."
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to remove that timeout.",
            ephemeral=True
        )


# ============================================================
# WARN
# ============================================================

@bot.tree.command(
    name="warn",
    description="Warn a Discord member."
)
@app_commands.describe(
    member="Member to warn",
    reason="Reason for the warning"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if member.id not in warnings:
        warnings[member.id] = []

    warnings[member.id].append(reason)

    count = len(
        warnings[member.id]
    )

    await interaction.response.send_message(
        f"⚠️ **{member}** has been warned.\n"
        f"**Reason:** {reason}\n"
        f"**Total warnings:** {count}"
    )


# ============================================================
# VIEW WARNINGS
# ============================================================

@bot.tree.command(
    name="warnings",
    description="View a member's warnings."
)
@app_commands.describe(
    member="Member to check"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def view_warnings(
    interaction: discord.Interaction,
    member: discord.Member
):

    user_warnings = warnings.get(
        member.id,
        []
    )

    if not user_warnings:

        await interaction.response.send_message(
            f"✅ **{member}** has no warnings."
        )
        return

    description = "\n".join(
        f"**{i}.** {reason}"
        for i, reason in enumerate(
            user_warnings,
            start=1
        )
    )

    embed = discord.Embed(
        title=f"⚠️ Warnings — {member}",
        description=description,
        color=discord.Color.orange()
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# CLEAR WARNINGS
# ============================================================

@bot.tree.command(
    name="clearwarnings",
    description="Clear all warnings from a member."
)
@app_commands.describe(
    member="Member whose warnings should be cleared"
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def clearwarnings(
    interaction: discord.Interaction,
    member: discord.Member
):

    warnings.pop(
        member.id,
        None
    )

    await interaction.response.send_message(
        f"✅ All warnings for **{member}** have been cleared."
    )


# ============================================================
# CLEAR MESSAGES
# ============================================================

@bot.tree.command(
    name="clear",
    description="Delete messages from a channel."
)
@app_commands.describe(
    amount="Number of messages to delete"
)
@app_commands.checks.has_permissions(
    manage_messages=True
)
async def clear(
    interaction: discord.Interaction,
    amount: app_commands.Range[int, 1, 100]
):

    await interaction.response.defer(
        ephemeral=True
    )

    deleted = await interaction.channel.purge(
        limit=amount
    )

    await interaction.followup.send(
        f"🧹 Deleted **{len(deleted)} messages**.",
        ephemeral=True
    )


# ============================================================
# LOCK
# ============================================================

@bot.tree.command(
    name="lock",
    description="Lock the current channel."
)
@app_commands.checks.has_permissions(
    manage_channels=True
)
async def lock(
    interaction: discord.Interaction
):

    channel = interaction.channel

    overwrite = channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = False

    await channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔒 This channel has been locked."
    )


# ============================================================
# UNLOCK
# ============================================================

@bot.tree.command(
    name="unlock",
    description="Unlock the current channel."
)
@app_commands.checks.has_permissions(
    manage_channels=True
)
async def unlock(
    interaction: discord.Interaction
):

    channel = interaction.channel

    overwrite = channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = None

    await channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔓 This channel has been unlocked."
    )


# ============================================================
# USER INFO
# ============================================================

@bot.tree.command(
    name="userinfo",
    description="Show information about a Discord member."
)
@app_commands.describe(
    member="Member to inspect"
)
async def userinfo(
    interaction: discord.Interaction,
    member: discord.Member
):

    embed = discord.Embed(
        title="👤 User Information",
        color=member.color
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="Username",
        value=str(member),
        inline=True
    )

    embed.add_field(
        name="User ID",
        value=str(member.id),
        inline=True
    )

    embed.add_field(
        name="Joined Server",
        value=discord.utils.format_dt(
            member.joined_at,
            style="F"
        ) if member.joined_at else "Unknown",
        inline=False
    )

    embed.add_field(
        name="Account Created",
        value=discord.utils.format_dt(
            member.created_at,
            style="F"
        ),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# SERVER INFO
# ============================================================

@bot.tree.command(
    name="serverinfo",
    description="Show information about this Discord server."
)
async def serverinfo(
    interaction: discord.Interaction
):

    guild = interaction.guild

    embed = discord.Embed(
        title=f"📊 {guild.name}",
        color=discord.Color.blue()
    )

    if guild.icon:
        embed.set_thumbnail(
            url=guild.icon.url
        )

    embed.add_field(
        name="Owner",
        value=f"<@{guild.owner_id}>",
        inline=True
    )

    embed.add_field(
        name="Members",
        value=str(guild.member_count),
        inline=True
    )

    embed.add_field(
        name="Channels",
        value=str(len(guild.channels)),
        inline=True
    )

    embed.add_field(
        name="Roles",
        value=str(len(guild.roles)),
        inline=True
    )

    embed.add_field(
        name="Server ID",
        value=str(guild.id),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# AVATAR
# ============================================================

@bot.tree.command(
    name="avatar",
    description="Show a member's avatar."
)
@app_commands.describe(
    member="Member whose avatar you want"
)
async def avatar(
    interaction: discord.Interaction,
    member: discord.Member
):

    embed = discord.Embed(
        title=f"🖼️ {member.display_name}'s Avatar"
    )

    embed.set_image(
        url=member.display_avatar.url
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# BOT INFO
# ============================================================

@bot.tree.command(
    name="botinfo",
    description="Show information about the bot."
)
async def botinfo(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="🤖 Ohio State Roleplay Utilities",
        description="ER:LC Discord Utility & Moderation Bot",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Bot",
        value=str(bot.user),
        inline=True
    )

    embed.add_field(
        name="Bot ID",
        value=str(bot.user.id),
        inline=True
    )

    embed.add_field(
        name="Latency",
        value=f"{round(bot.latency * 1000)}ms",
        inline=True
    )

    embed.add_field(
        name="Commands",
        value=str(len(bot.tree.get_commands())),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# ERROR HANDLER
# ============================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):

        message = (
            "❌ You don't have permission "
            "to use this command."
        )

    elif isinstance(
        error,
        app_commands.CheckFailure
    ):

        message = (
            "❌ You don't have permission "
            "to use this command."
        )

    else:

        print(
            f"COMMAND ERROR: {error}"
        )

        message = (
            "❌ An error occurred "
            "while running this command."
        )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                message,
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

    except Exception as error:

        print(
            f"ERROR HANDLER ERROR: {error}"
        )


# ============================================================
# START BOT
# ============================================================

print(
    "TOKEN LOADED:",
    bool(DISCORD_TOKEN)
)

print(
    "TOKEN LENGTH:",
    len(DISCORD_TOKEN)
)

bot.run(
    DISCORD_TOKEN
)

