

import os
from datetime import timedelta

import discord
from discord import app_commands
from dotenv import load_dotenv
from erlc_api import AsyncClient


# =========================================================
# LOAD .ENV
# =========================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ERLC_SERVER_KEY = os.getenv("ERLC_SERVER_KEY")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing from .env")

if not ERLC_SERVER_KEY:
    raise ValueError("ERLC_SERVER_KEY is missing from .env")


# =========================================================
# SETTINGS
# =========================================================

# REQUIRED DISCORD ROLE
API_ROLE_ID = 1556029577342484531


# =========================================================
# DISCORD CLIENT
# =========================================================

# We only use slash commands, so Message Content Intent
# is NOT required.
intents = discord.Intents.default()

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


# =========================================================
# ER:LC API CLIENT
# =========================================================

erlc = AsyncClient(server_key=ERLC_SERVER_KEY)


# =========================================================
# GLOBAL API ROLE CHECK
# =========================================================

@tree.interaction_check
async def api_role_check(interaction: discord.Interaction) -> bool:

    # Commands can only be used inside a Discord server
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This bot can only be used inside a Discord server.",
            ephemeral=True
        )
        return False

    # Slash-command interactions in a guild normally provide
    # the user as a Member.
    member = interaction.user

    if not isinstance(member, discord.Member):
        await interaction.response.send_message(
            "❌ I couldn't verify your Discord role.",
            ephemeral=True
        )
        return False

    # Check for the required role
    has_role = any(
        role.id == API_ROLE_ID
        for role in member.roles
    )

    if not has_role:
        await interaction.response.send_message(
            "❌ You don't have permission to use this bot.\n"
            f"You need the <@&{API_ROLE_ID}> role.",
            ephemeral=True
        )
        return False

    return True


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")

    try:
        synced = await tree.sync()

        print(f"Synced {len(synced)} slash commands.")

    except Exception as error:
        print(f"Failed to sync slash commands: {error}")

    print("Bot is online!")


# =========================================================
# PING
# =========================================================

@tree.command(
    name="ping",
    description="Check the bot's latency."
)
async def ping(interaction: discord.Interaction):

    latency = round(bot.latency * 1000)

    await interaction.response.send_message(
        f"🏓 Pong! `{latency}ms`"
    )


# =========================================================
# BOT INFO
# =========================================================

@tree.command(
    name="botinfo",
    description="Show information about the bot."
)
async def botinfo(interaction: discord.Interaction):

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
        name="Discord Servers",
        value=str(len(bot.guilds)),
        inline=True
    )

    embed.add_field(
        name="Required Role",
        value=f"<@&{API_ROLE_ID}>",
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# USER INFO
# =========================================================

@tree.command(
    name="userinfo",
    description="Show information about a Discord user."
)
@app_commands.describe(
    user="The user to view."
)
async def userinfo(
    interaction: discord.Interaction,
    user: discord.Member
):

    embed = discord.Embed(
        title="👤 User Information",
        color=discord.Color.blue()
    )

    embed.set_thumbnail(
        url=user.display_avatar.url
    )

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

    if user.joined_at:
        joined = discord.utils.format_dt(
            user.joined_at,
            "F"
        )
    else:
        joined = "Unknown"

    embed.add_field(
        name="Joined Server",
        value=joined,
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# AVATAR
# =========================================================

@tree.command(
    name="avatar",
    description="Show a user's avatar."
)
@app_commands.describe(
    user="The user whose avatar you want."
)
async def avatar(
    interaction: discord.Interaction,
    user: discord.Member
):

    embed = discord.Embed(
        title=f"{user.display_name}'s Avatar",
        color=discord.Color.blue()
    )

    embed.set_image(
        url=user.display_avatar.url
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# SERVER INFO
# =========================================================

@tree.command(
    name="serverinfo",
    description="Show Discord server information."
)
async def serverinfo(interaction: discord.Interaction):

    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🏠 Discord Server Information",
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

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# BAN
# =========================================================

@tree.command(
    name="ban",
    description="Ban a Discord member."
)
@app_commands.describe(
    user="The member to ban.",
    reason="Reason for the ban."
)
async def ban(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You need the **Ban Members** permission.",
            ephemeral=True
        )
        return

    try:

        await user.ban(
            reason=reason
        )

        await interaction.response.send_message(
            f"🔨 **{user}** has been banned.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to ban this user.",
            ephemeral=True
        )


# =========================================================
# UNBAN
# =========================================================

@tree.command(
    name="unban",
    description="Unban a Discord user."
)
@app_commands.describe(
    user_id="The Discord user ID.",
    reason="Reason for the unban."
)
async def unban(
    interaction: discord.Interaction,
    user_id: str,
    reason: str = "No reason provided"
):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You need the **Ban Members** permission.",
            ephemeral=True
        )
        return

    try:

        user = await bot.fetch_user(
            int(user_id)
        )

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
            "❌ That isn't a valid Discord user ID.",
            ephemeral=True
        )

    except discord.NotFound:

        await interaction.response.send_message(
            "❌ That user isn't banned.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to unban users.",
            ephemeral=True
        )


# =========================================================
# KICK
# =========================================================

@tree.command(
    name="kick",
    description="Kick a Discord member."
)
@app_commands.describe(
    user="The member to kick.",
    reason="Reason for the kick."
)
async def kick(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            "❌ You need the **Kick Members** permission.",
            ephemeral=True
        )
        return

    try:

        await user.kick(
            reason=reason
        )

        await interaction.response.send_message(
            f"👢 **{user}** has been kicked.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to kick this user.",
            ephemeral=True
        )


# =========================================================
# TIMEOUT
# =========================================================

@tree.command(
    name="timeout",
    description="Timeout a Discord member."
)
@app_commands.describe(
    user="The member to timeout.",
    minutes="How many minutes.",
    reason="Reason for the timeout."
)
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    minutes: int,
    reason: str = "No reason provided"
):

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You need the **Moderate Members** permission.",
            ephemeral=True
        )
        return

    if minutes < 1 or minutes > 40320:
        await interaction.response.send_message(
            "❌ Timeout must be between 1 and 40320 minutes.",
            ephemeral=True
        )
        return

    try:

        await user.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        await interaction.response.send_message(
            f"⏱️ **{user}** has been timed out for "
            f"**{minutes} minutes**.\n"
            f"**Reason:** {reason}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to timeout this user.",
            ephemeral=True
        )


# =========================================================
# UNTIMEOUT
# =========================================================

@tree.command(
    name="untimeout",
    description="Remove a timeout from a Discord member."
)
@app_commands.describe(
    user="The member to untimeout."
)
async def untimeout(
    interaction: discord.Interaction,
    user: discord.Member
):

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You need the **Moderate Members** permission.",
            ephemeral=True
        )
        return

    try:

        await user.timeout(
            None
        )

        await interaction.response.send_message(
            f"✅ Timeout removed from **{user}**."
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to remove the timeout.",
            ephemeral=True
        )


# =========================================================
# WARN SYSTEM
# =========================================================

warnings = {}


@tree.command(
    name="warn",
    description="Warn a Discord member."
)
@app_commands.describe(
    user="The member to warn.",
    reason="Reason for the warning."
)
async def warn(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided"
):

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You need the **Moderate Members** permission.",
            ephemeral=True
        )
        return

    if user.id not in warnings:
        warnings[user.id] = []

    warnings[user.id].append(reason)

    total = len(
        warnings[user.id]
    )

    await interaction.response.send_message(
        f"⚠️ **{user}** has been warned.\n"
        f"**Reason:** {reason}\n"
        f"**Total warnings:** {total}"
    )


@tree.command(
    name="warnings",
    description="View a user's warnings."
)
@app_commands.describe(
    user="The member to check."
)
async def show_warnings(
    interaction: discord.Interaction,
    user: discord.Member
):

    user_warnings = warnings.get(
        user.id,
        []
    )

    if not user_warnings:

        await interaction.response.send_message(
            f"✅ **{user}** has no warnings."
        )
        return

    description = ""

    for number, reason in enumerate(
        user_warnings,
        start=1
    ):

        description += (
            f"**{number}.** {reason}\n"
        )

    embed = discord.Embed(
        title=f"⚠️ Warnings for {user}",
        description=description,
        color=discord.Color.orange()
    )

    await interaction.response.send_message(
        embed=embed
    )


@tree.command(
    name="clearwarnings",
    description="Clear all warnings from a user."
)
@app_commands.describe(
    user="The member whose warnings should be cleared."
)
async def clearwarnings(
    interaction: discord.Interaction,
    user: discord.Member
):

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You need the **Moderate Members** permission.",
            ephemeral=True
        )
        return

    warnings.pop(
        user.id,
        None
    )

    await interaction.response.send_message(
        f"✅ Warnings cleared for **{user}**."
    )


# =========================================================
# CLEAR MESSAGES
# =========================================================

@tree.command(
    name="clear",
    description="Delete messages from the current channel."
)
@app_commands.describe(
    amount="Number of messages to delete."
)
async def clear(
    interaction: discord.Interaction,
    amount: int
):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ You need the **Manage Messages** permission.",
            ephemeral=True
        )
        return

    if amount < 1 or amount > 100:
        await interaction.response.send_message(
            "❌ Amount must be between 1 and 100.",
            ephemeral=True
        )
        return

    if not isinstance(
        interaction.channel,
        discord.TextChannel
    ):
        await interaction.response.send_message(
            "❌ This command can only be used in a text channel.",
            ephemeral=True
        )
        return

    await interaction.response.defer(
        ephemeral=True
    )

    try:

        deleted = await interaction.channel.purge(
            limit=amount
        )

        await interaction.followup.send(
            f"🧹 Deleted **{len(deleted)} messages**.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.followup.send(
            "❌ I don't have permission to delete messages.",
            ephemeral=True
        )


# =========================================================
# LOCK CHANNEL
# =========================================================

@tree.command(
    name="lock",
    description="Lock the current channel."
)
async def lock(
    interaction: discord.Interaction
):

    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message(
            "❌ You need the **Manage Channels** permission.",
            ephemeral=True
        )
        return

    channel = interaction.channel

    if not isinstance(
        channel,
        discord.TextChannel
    ):
        await interaction.response.send_message(
            "❌ This command can only be used in a text channel.",
            ephemeral=True
        )
        return

    overwrite = channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = False

    await channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔒 Channel locked."
    )


# =========================================================
# UNLOCK CHANNEL
# =========================================================

@tree.command(
    name="unlock",
    description="Unlock the current channel."
)
async def unlock(
    interaction: discord.Interaction
):

    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message(
            "❌ You need the **Manage Channels** permission.",
            ephemeral=True
        )
        return

    channel = interaction.channel

    if not isinstance(
        channel,
        discord.TextChannel
    ):
        await interaction.response.send_message(
            "❌ This command can only be used in a text channel.",
            ephemeral=True
        )
        return

    overwrite = channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = None

    await channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔓 Channel unlocked."
    )


# =========================================================
# ER:LC SERVER
# =========================================================

@tree.command(
    name="server",
    description="Get information about the ER:LC server."
)
async def server(
    interaction: discord.Interaction
):

    await interaction.response.defer()

    try:

        # Get server information
        server_data = await erlc.server()

        # Get current players separately.
        # This avoids using properties that don't exist
        # on the ServerBundle/Server object.
        player_data = await erlc.players()

        server_name = getattr(
            server_data,
            "name",
            "Unknown"
        )

        player_count = len(
            player_data
        )

        embed = discord.Embed(
            title="🚓 ER:LC Server",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Server Name",
            value=str(server_name),
            inline=False
        )

        embed.add_field(
            name="Players",
            value=str(player_count),
            inline=True
        )

        embed.add_field(
            name="API Status",
            value="🟢 Online",
            inline=True
        )

        await interaction.followup.send(
            embed=embed
        )

    except Exception as error:

        print(
            f"/server error: {error}"
        )

        await interaction.followup.send(
            "❌ Failed to get ER:LC server information.\n"
            f"```{error}```"
        )


# =========================================================
# ER:LC PLAYERS
# =========================================================

@tree.command(
    name="players",
    description="Show players currently in the ER:LC server."
)
async def players(
    interaction: discord.Interaction
):

    await interaction.response.defer()

    try:

        player_data = await erlc.players()

        if not player_data:

            await interaction.followup.send(
                "👥 There are currently no players in the server."
            )
            return

        player_list = ""

        for player in player_data:

            player_name = getattr(
                player,
                "name",
                "Unknown"
            )

            player_team = getattr(
                player,
                "team",
                "Unknown"
            )

            player_list += (
                f"• **{player_name}** — `{player_team}`\n"
            )

        # Discord embeds have a description limit.
        if len(player_list) > 4000:
            player_list = (
                player_list[:3950]
                + "\n...and more."
            )

        embed = discord.Embed(
            title=f"👥 ER:LC Players ({len(player_data)})",
            description=player_list,
            color=discord.Color.blue()
        )

        await interaction.followup.send(
            embed=embed
        )

    except Exception as error:

        print(
            f"/players error: {error}"
        )

        await interaction.followup.send(
            "❌ Failed to get ER:LC players.\n"
            f"```{error}```"
        )


# =========================================================
# ER:LC ANNOUNCE
# =========================================================

@tree.command(
    name="announce",
    description="Send an announcement in ER:LC."
)
@app_commands.describe(
    message="The announcement to send."
)
async def announce(
    interaction: discord.Interaction,
    message: str
):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You need the **Manage Server** permission.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:

        result = await erlc.command(
            f":h {message}"
        )

        success = getattr(
            result,
            "success",
            True
        )

        result_message = getattr(
            result,
            "message",
            str(result)
        )

        if success:

            await interaction.followup.send(
                f"📢 **Announcement sent!**\n"
                f"> {message}"
            )

        else:

            await interaction.followup.send(
                f"❌ ER:LC rejected the command.\n"
                f"```{result_message}```"
            )

    except Exception as error:

        print(
            f"/announce error: {error}"
        )

        await interaction.followup.send(
            "❌ Failed to send announcement.\n"
            f"```{error}```"
        )


# =========================================================
# ER:LC RAW COMMAND
# =========================================================

@tree.command(
    name="command",
    description="Send a command directly to ER:LC."
)
@app_commands.describe(
    command_text="The ER:LC command to execute."
)
async def raw_command(
    interaction: discord.Interaction,
    command_text: str
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need **Administrator** permission to use this command.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:

        result = await erlc.command(
            command_text
        )

        success = getattr(
            result,
            "success",
            True
        )

        result_message = getattr(
            result,
            "message",
            str(result)
        )

        if success:

            await interaction.followup.send(
                f"✅ **Command executed.**\n"
                f"```{result_message}```"
            )

        else:

            await interaction.followup.send(
                f"❌ **Command failed.**\n"
                f"```{result_message}```"
            )

    except Exception as error:

        print(
            f"/command error: {error}"
        )

        await interaction.followup.send(
            "❌ Failed to execute ER:LC command.\n"
            f"```{error}```"
        )


# =========================================================
# ER:LC KICK PLAYER
# =========================================================

@tree.command(
    name="kickplayer",
    description="Kick a player from ER:LC."
)
@app_commands.describe(
    username="The ER:LC username.",
    reason="Reason for the kick."
)
async def kickplayer(
    interaction: discord.Interaction,
    username: str,
    reason: str = "No reason provided"
):

    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            "❌ You need the **Kick Members** permission.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:

        result = await erlc.command(
            f":kick {username} {reason}"
        )

        success = getattr(
            result,
            "success",
            True
        )

        result_message = getattr(
            result,
            "message",
            str(result)
        )

        if success:

            await interaction.followup.send(
                f"👢 **{username}** was kicked from ER:LC.\n"
                f"**Reason:** {reason}"
            )

        else:

            await interaction.followup.send(
                f"❌ ER:LC rejected the kick.\n"
                f"```{result_message}```"
            )

    except Exception as error:

        await interaction.followup.send(
            "❌ Failed to kick player.\n"
            f"```{error}```"
        )


# =========================================================
# ER:LC BAN PLAYER
# =========================================================

@tree.command(
    name="banplayer",
    description="Ban a player from ER:LC."
)
@app_commands.describe(
    username="The ER:LC username.",
    reason="Reason for the ban."
)
async def banplayer(
    interaction: discord.Interaction,
    username: str,
    reason: str = "No reason provided"
):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You need the **Ban Members** permission.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:

        result = await erlc.command(
            f":ban {username} {reason}"
        )

        success = getattr(
            result,
            "success",
            True
        )

        result_message = getattr(
            result,
            "message",
            str(result)
        )

        if success:

            await interaction.followup.send(
                f"🔨 **{username}** was banned from ER:LC.\n"
                f"**Reason:** {reason}"
            )

        else:

            await interaction.followup.send(
                f"❌ ER:LC rejected the ban.\n"
                f"```{result_message}```"
            )

    except Exception as error:

        await interaction.followup.send(
            "❌ Failed to ban player.\n"
            f"```{error}```"
        )


# =========================================================
# ER:LC UNBAN PLAYER
# =========================================================

@tree.command(
    name="unbanplayer",
    description="Unban a player from ER:LC."
)
@app_commands.describe(
    username="The ER:LC username."
)
async def unbanplayer(
    interaction: discord.Interaction,
    username: str
):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You need the **Ban Members** permission.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:

        result = await erlc.command(
            f":unban {username}"
        )

        success = getattr(
            result,
            "success",
            True
        )

        result_message = getattr(
            result,
            "message",
            str(result)
        )

        if success:

            await interaction.followup.send(
                f"🔓 **{username}** was unbanned from ER:LC."
            )

        else:

            await interaction.followup.send(
                f"❌ ER:LC rejected the unban.\n"
                f"```{result_message}```"
            )

    except Exception as error:

        await interaction.followup.send(
            "❌ Failed to unban player.\n"
            f"```{error}```"
        )


# =========================================================
# ERROR HANDLER
# =========================================================

@tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    print(
        f"Command error: {error}"
    )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                f"❌ An error occurred:\n"
                f"```{error}```",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                f"❌ An error occurred:\n"
                f"```{error}```",
                ephemeral=True
            )

    except Exception as handler_error:

        print(
            f"Error handler failed: {handler_error}"
        )


# =========================================================
# START BOT
# =========================================================

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
