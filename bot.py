

import os
from datetime import timedelta

import discord
from discord import app_commands
from dotenv import load_dotenv
from erlc_api import AsyncClient


# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ERLC_SERVER_KEY = os.getenv("ERLC_SERVER_KEY")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing from .env")

if not ERLC_SERVER_KEY:
    raise ValueError("ERLC_SERVER_KEY is missing from .env")


# =========================
# SETTINGS
# =========================

# Role required to use ANY bot command
API_ROLE_ID = 1556029577342484531


# =========================
# DISCORD CLIENT
# =========================

intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

erlc = AsyncClient(server_key=ERLC_SERVER_KEY)


# =========================
# API ROLE CHECK
# =========================

def has_api_role(interaction: discord.Interaction) -> bool:
    """Check if the user has the required API role."""

    if not interaction.guild:
        return False

    member = interaction.guild.get_member(interaction.user.id)

    if not member:
        return False

    return any(role.id == API_ROLE_ID for role in member.roles)


async def check_api_role(interaction: discord.Interaction) -> bool:
    """Send an error message if the user doesn't have the API role."""

    if has_api_role(interaction):
        return True

    if interaction.response.is_done():
        await interaction.followup.send(
            "❌ You need the required API role to use this bot.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ You need the required API role to use this bot.",
            ephemeral=True
        )

    return False


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")

    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as error:
        print(f"Failed to sync commands: {error}")

    print("Bot is online!")


# =========================
# PING
# =========================

@tree.command(name="ping", description="Check the bot's latency.")
async def ping(interaction: discord.Interaction):

    if not await check_api_role(interaction):
        return

    latency = round(bot.latency * 1000)

    await interaction.response.send_message(
        f"🏓 Pong! `{latency}ms`"
    )


# =========================
# BOT INFO
# =========================

@tree.command(name="botinfo", description="Show information about the bot.")
async def botinfo(interaction: discord.Interaction):

    if not await check_api_role(interaction):
        return

    embed = discord.Embed(
        title="🤖 Bot Information",
        description="Ohio State Roleplay Utilities",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Bot",
        value=str(bot.user),
        inline=False
    )

    embed.add_field(
        name="Bot ID",
        value=str(bot.user.id),
        inline=False
    )

    embed.add_field(
        name="Servers",
        value=str(len(bot.guilds)),
        inline=True
    )

    embed.add_field(
        name="API Role",
        value=f"<@&{API_ROLE_ID}>",
        inline=True
    )

    await interaction.response.send_message(embed=embed)


# =========================
# USER INFO
# =========================

@tree.command(name="userinfo", description="Show information about a Discord user.")
@app_commands.describe(user="The user to view.")
async def userinfo(
    interaction: discord.Interaction,
    user: discord.Member
):

    if not await check_api_role(interaction):
        return

    embed = discord.Embed(
        title="👤 User Information",
        color=discord.Color.blue()
    )

    embed.set_thumbnail(url=user.display_avatar.url)

    embed.add_field(
        name="Username",
        value=str(user),
        inline=True
    )

    embed.add_field(
        name="User ID",
        value=str(user.id),
        inline=True
    )

    embed.add_field(
        name="Joined Server",
        value=discord.utils.format_dt(user.joined_at, "F")
        if user.joined_at else "Unknown",
        inline=False
    )

    await interaction.response.send_message(embed=embed)


# =========================
# AVATAR
# =========================

@tree.command(name="avatar", description="Show a user's avatar.")
@app_commands.describe(user="The user whose avatar you want.")
async def avatar(
    interaction: discord.Interaction,
    user: discord.Member
):

    if not await check_api_role(interaction):
        return

    embed = discord.Embed(
        title=f"{user.display_name}'s Avatar",
        color=discord.Color.blue()
    )

    embed.set_image(url=user.display_avatar.url)

    await interaction.response.send_message(embed=embed)


# =========================
# SERVER INFO
# =========================

@tree.command(name="serverinfo", description="Show Discord server information.")
async def serverinfo(interaction: discord.Interaction):

    if not await check_api_role(interaction):
        return

    guild = interaction.guild

    if not guild:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🏠 Server Information",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Server",
        value=guild.name,
        inline=True
    )

    embed.add_field(
        name="Server ID",
        value=str(guild.id),
        inline=True
    )

    embed.add_field(
        name="Members",
        value=str(guild.member_count),
        inline=True
    )

    embed.add_field(
        name="Owner",
        value=f"<@{guild.owner_id}>",
        inline=True
    )

    await interaction.response.send_message(embed=embed)


# =========================
# BAN
# =========================

@tree.command(name="ban", description="Ban a Discord member.")
@app_commands.describe(
    user="The member to ban.",
    reason="Reason for the ban."
)
async def ban(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You need the Ban Members permission.",
            ephemeral=True
        )
        return

    try:
        await user.ban(reason=reason)

        await interaction.response.send_message(
            f"🔨 **{user}** has been banned.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to ban this user.",
            ephemeral=True
        )


# =========================
# UNBAN
# =========================

@tree.command(name="unban", description="Unban a Discord user.")
@app_commands.describe(
    user_id="The ID of the user to unban.",
    reason="Reason for the unban."
)
async def unban(
    interaction: discord.Interaction,
    user_id: str,
    reason: str = "No reason provided"
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You need the Ban Members permission.",
            ephemeral=True
        )
        return

    try:
        user = await bot.fetch_user(int(user_id))

        await interaction.guild.unban(
            user,
            reason=reason
        )

        await interaction.response.send_message(
            f"🔓 **{user}** has been unbanned.\n"
            f"**Reason:** {reason}"
        )

    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid user ID.",
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


# =========================
# KICK
# =========================

@tree.command(name="kick", description="Kick a Discord member.")
@app_commands.describe(
    user="The member to kick.",
    reason="Reason for the kick."
)
async def kick(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            "❌ You need the Kick Members permission.",
            ephemeral=True
        )
        return

    try:
        await user.kick(reason=reason)

        await interaction.response.send_message(
            f"👢 **{user}** has been kicked.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to kick this user.",
            ephemeral=True
        )


# =========================
# TIMEOUT
# =========================

@tree.command(name="timeout", description="Timeout a Discord member.")
@app_commands.describe(
    user="The member to timeout.",
    minutes="How many minutes to timeout them.",
    reason="Reason for the timeout."
)
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    minutes: int,
    reason: str = "No reason provided"
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You need the Moderate Members permission.",
            ephemeral=True
        )
        return

    if minutes < 1 or minutes > 40320:
        await interaction.response.send_message(
            "❌ Timeout duration must be between 1 and 40320 minutes.",
            ephemeral=True
        )
        return

    try:
        await user.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏱️ **{user}** has been timed out for **{minutes} minutes**.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to timeout this user.",
            ephemeral=True
        )


# =========================
# UNTIMEOUT
# =========================

@tree.command(name="untimeout", description="Remove a timeout from a member.")
@app_commands.describe(user="The member to untimeout.")
async def untimeout(
    interaction: discord.Interaction,
    user: discord.Member
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You need the Moderate Members permission.",
            ephemeral=True
        )
        return

    try:
        await user.timeout(None)

        await interaction.response.send_message(
            f"✅ Timeout removed from **{user}**."
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to remove this timeout.",
            ephemeral=True
        )


# =========================
# WARNINGS
# =========================

warnings = {}


@tree.command(name="warn", description="Warn a Discord member.")
@app_commands.describe(
    user="The member to warn.",
    reason="Reason for the warning."
)
async def warn(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You need the Moderate Members permission.",
            ephemeral=True
        )
        return

    if user.id not in warnings:
        warnings[user.id] = []

    warnings[user.id].append(reason)

    count = len(warnings[user.id])

    await interaction.response.send_message(
        f"⚠️ **{user}** has been warned.\n"
        f"**Reason:** {reason}\n"
        f"**Total warnings:** {count}"
    )


@tree.command(name="warnings", description="View a user's warnings.")
@app_commands.describe(user="The member to view.")
async def show_warnings(
    interaction: discord.Interaction,
    user: discord.Member
):

    if not await check_api_role(interaction):
        return

    user_warnings = warnings.get(user.id, [])

    if not user_warnings:
        await interaction.response.send_message(
            f"✅ **{user}** has no warnings."
        )
        return

    description = ""

    for number, reason in enumerate(user_warnings, start=1):
        description += f"**{number}.** {reason}\n"

    embed = discord.Embed(
        title=f"⚠️ Warnings for {user}",
        description=description,
        color=discord.Color.orange()
    )

    await interaction.response.send_message(embed=embed)


@tree.command(name="clearwarnings", description="Clear all warnings from a user.")
@app_commands.describe(user="The member whose warnings should be cleared.")
async def clearwarnings(
    interaction: discord.Interaction,
    user: discord.Member
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You need the Moderate Members permission.",
            ephemeral=True
        )
        return

    warnings.pop(user.id, None)

    await interaction.response.send_message(
        f"✅ Warnings cleared for **{user}**."
    )


# =========================
# CLEAR MESSAGES
# =========================

@tree.command(name="clear", description="Delete messages from a channel.")
@app_commands.describe(amount="Number of messages to delete.")
async def clear(
    interaction: discord.Interaction,
    amount: int
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ You need the Manage Messages permission.",
            ephemeral=True
        )
        return

    if amount < 1 or amount > 100:
        await interaction.response.send_message(
            "❌ Amount must be between 1 and 100.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    deleted = await interaction.channel.purge(limit=amount)

    await interaction.followup.send(
        f"🧹 Deleted **{len(deleted)} messages**.",
        ephemeral=True
    )


# =========================
# LOCK
# =========================

@tree.command(name="lock", description="Lock the current channel.")
async def lock(interaction: discord.Interaction):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message(
            "❌ You need the Manage Channels permission.",
            ephemeral=True
        )
        return

    overwrite = interaction.channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = False

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔒 Channel locked."
    )


# =========================
# UNLOCK
# =========================

@tree.command(name="unlock", description="Unlock the current channel.")
async def unlock(interaction: discord.Interaction):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message(
            "❌ You need the Manage Channels permission.",
            ephemeral=True
        )
        return

    overwrite = interaction.channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = None

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔓 Channel unlocked."
    )


# =========================
# ER:LC SERVER
# =========================

@tree.command(name="server", description="Get information about the ER:LC server.")
async def server(interaction: discord.Interaction):

    if not await check_api_role(interaction):
        return

    await interaction.response.defer()

    try:
        server_data = await erlc.server()

        embed = discord.Embed(
            title="🚓 ER:LC Server",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Name",
            value=str(server_data.name),
            inline=False
        )

        embed.add_field(
            name="Players",
            value=f"{server_data.current_players}/{server_data.max_players}",
            inline=True
        )

        embed.add_field(
            name="Join Code",
            value=str(server_data.join_code),
            inline=True
        )

        await interaction.followup.send(embed=embed)

    except Exception as error:
        await interaction.followup.send(
            f"❌ Failed to get the ER:LC server information.\n```{error}```"
        )


# =========================
# ER:LC PLAYERS
# =========================

@tree.command(name="players", description="Show players currently in the ER:LC server.")
async def players(interaction: discord.Interaction):

    if not await check_api_role(interaction):
        return

    await interaction.response.defer()

    try:
        player_data = await erlc.players()

        if not player_data:
            await interaction.followup.send(
                "There are currently no players in the server."
            )
            return

        player_list = ""

        for player in player_data:
            player_list += f"• **{player.player}** — `{player.team}`\n"

        embed = discord.Embed(
            title="👮 ER:LC Players",
            description=player_list,
            color=discord.Color.blue()
        )

        await interaction.followup.send(embed=embed)

    except Exception as error:
        await interaction.followup.send(
            f"❌ Failed to get players.\n```{error}```"
        )


# =========================
# ER:LC ANNOUNCE
# =========================

@tree.command(name="announce", description="Send an announcement in ER:LC.")
@app_commands.describe(message="The announcement to send.")
async def announce(
    interaction: discord.Interaction,
    message: str
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You need the Manage Server permission.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        await erlc.command(f":h {message}")

        await interaction.followup.send(
            f"📢 Announcement sent:\n> {message}"
        )

    except Exception as error:
        await interaction.followup.send(
            f"❌ Failed to send announcement.\n```{error}```"
        )


# =========================
# ER:LC COMMAND
# =========================

@tree.command(name="command", description="Send a command directly to ER:LC.")
@app_commands.describe(command="The ER:LC command to execute.")
async def command(
    interaction: discord.Interaction,
    command: str
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need Administrator permission to use this command.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        result = await erlc.command(command)

        await interaction.followup.send(
            f"✅ Command sent.\n```{result}```"
        )

    except Exception as error:
        await interaction.followup.send(
            f"❌ Failed to execute command.\n```{error}```"
        )


# =========================
# ER:LC KICK PLAYER
# =========================

@tree.command(name="kickplayer", description="Kick a player from ER:LC.")
@app_commands.describe(
    username="The ER:LC username to kick.",
    reason="Reason for the kick."
)
async def kickplayer(
    interaction: discord.Interaction,
    username: str,
    reason: str = "No reason provided"
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            "❌ You need the Kick Members permission.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        await erlc.command(f":kick {username} {reason}")

        await interaction.followup.send(
            f"👢 **{username}** has been kicked from ER:LC.\n"
            f"**Reason:** {reason}"
        )

    except Exception as error:
        await interaction.followup.send(
            f"❌ Failed to kick player.\n```{error}```"
        )


# =========================
# ER:LC BAN PLAYER
# =========================

@tree.command(name="banplayer", description="Ban a player from ER:LC.")
@app_commands.describe(
    username="The ER:LC username to ban.",
    reason="Reason for the ban."
)
async def banplayer(
    interaction: discord.Interaction,
    username: str,
    reason: str = "No reason provided"
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You need the Ban Members permission.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        await erlc.command(f":ban {username} {reason}")

        await interaction.followup.send(
            f"🔨 **{username}** has been banned from ER:LC.\n"
            f"**Reason:** {reason}"
        )

    except Exception as error:
        await interaction.followup.send(
            f"❌ Failed to ban player.\n```{error}```"
        )


# =========================
# ER:LC UNBAN PLAYER
# =========================

@tree.command(name="unbanplayer", description="Unban a player from ER:LC.")
@app_commands.describe(username="The ER:LC username to unban.")
async def unbanplayer(
    interaction: discord.Interaction,
    username: str
):

    if not await check_api_role(interaction):
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You need the Ban Members permission.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        await erlc.command(f":unban {username}")

        await interaction.followup.send(
            f"🔓 **{username}** has been unbanned from ER:LC."
        )

    except Exception as error:
        await interaction.followup.send(
            f"❌ Failed to unban player.\n```{error}```"
        )


# =========================
# ERROR HANDLER
# =========================

@tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    print(f"Command error: {error}")

    if interaction.response.is_done():
        await interaction.followup.send(
            f"❌ An error occurred:\n```{error}```",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ An error occurred:\n```{error}```",
            ephemeral=True
        )


# =========================
# START BOT
# =========================

print("TOKEN LOADED:", bool(DISCORD_TOKEN))
print("TOKEN LENGTH:", len(DISCORD_TOKEN))

bot.run(DISCORD_TOKEN)
