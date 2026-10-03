import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from erlc_api import AsyncClient

# Load .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ERLC_SERVER_KEY = os.getenv("ERLC_SERVER_KEY")

# Check configuration
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")

if not ERLC_SERVER_KEY:
    raise RuntimeError("ERLC_SERVER_KEY is missing from .env")


# Discord bot
intents = discord.Intents.default()

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")

    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print("Bot is online!")


# /ping
@tree.command(name="ping", description="Check if the bot is online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")


# /server
@tree.command(name="server", description="Show the ER:LC server information.")
async def server(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with AsyncClient(server_key=ERLC_SERVER_KEY) as api:
            server_info = await api.server()

        embed = discord.Embed(
            title="🚓 ER:LC Server",
            description="Current server information",
            color=discord.Color.blue()
        )

        # Try to get common values safely
        name = getattr(server_info, "name", None)
        current_players = getattr(server_info, "current_players", None)
        max_players = getattr(server_info, "max_players", None)

        if name:
            embed.add_field(
                name="Server",
                value=str(name),
                inline=False
            )

        if current_players is not None and max_players is not None:
            embed.add_field(
                name="Players",
                value=f"{current_players}/{max_players}",
                inline=True
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"ER:LC API error: {e}")
        await interaction.followup.send(
            "❌ I couldn't connect to the ER:LC server. "
            "Check your ERLC_SERVER_KEY."
        )


# /players
@tree.command(name="players", description="Show players currently in the ER:LC server.")
async def players(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with AsyncClient(server_key=ERLC_SERVER_KEY) as api:
            players = await api.players()

        if not players:
            await interaction.followup.send("👤 There are currently no players.")
            return

        player_lines = []

        for player in players:
            player_name = getattr(player, "name", "Unknown")
            player_id = getattr(player, "id", "Unknown")

            player_lines.append(
                f"**{player_name}** (`{player_id}`)"
            )

        # Discord messages have a character limit
        message = "\n".join(player_lines)

        if len(message) > 1900:
            message = message[:1900] + "\n..."

        embed = discord.Embed(
            title="👥 ER:LC Players",
            description=message,
            color=discord.Color.green()
        )

        embed.set_footer(text=f"{len(players)} player(s) online")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"ER:LC API error: {e}")
        await interaction.followup.send(
            "❌ I couldn't get the player list. "
            "Check your ERLC_SERVER_KEY."
        )


# /announce
@tree.command(
    name="announce",
    description="Send an announcement to the ER:LC server."
)
@app_commands.describe(message="The message to announce")
async def announce(
    interaction: discord.Interaction,
    message: str
):
    # Only allow people with Manage Server
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You need **Manage Server** permission to use this command.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        async with AsyncClient(server_key=ERLC_SERVER_KEY) as api:
            result = await api.command(f":h {message}")

        print(f"ER:LC command result: {result}")

        await interaction.followup.send(
            "✅ Announcement sent to the ER:LC server."
        )

    except Exception as e:
        print(f"ER:LC command error: {e}")

        await interaction.followup.send(
            "❌ I couldn't send the announcement. "
            "Your ER:LC API may need Remote Server Management authorization."
        )


@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Discord error in {event}")


# Start bot
bot.run(DISCORD_TOKEN)
