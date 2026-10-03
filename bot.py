import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from erlc_api import AsyncClient

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ERLC_SERVER_KEY = os.getenv("ERLC_SERVER_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")

if not ERLC_SERVER_KEY:
    raise RuntimeError("ERLC_SERVER_KEY is missing from .env")


class ERLCBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

        self.erlc = AsyncClient(
            server_key=ERLC_SERVER_KEY
        )

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced.")


bot = ERLCBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("ER:LC Discord bot is online.")


@bot.tree.command(name="players", description="Show players currently in ER:LC")
async def players(interaction: discord.Interaction):

    await interaction.response.defer()

    try:
        players = await bot.erlc.players()

        if not players:
            await interaction.followup.send(
                "There are currently no players in the ER:LC server."
            )
            return

        player_list = "\n".join(
            f"• {player.name} (`{player.user_id}`)"
            for player in players
        )

        embed = discord.Embed(
            title="🚔 ER:LC Players",
            description=player_list
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(
            f"❌ API error: `{e}`"
        )


@bot.tree.command(name="server", description="Show ER:LC server information")
async def server(interaction: discord.Interaction):

    await interaction.response.defer()

    try:
        server = await bot.erlc.server()

        embed = discord.Embed(
            title="🚔 ER:LC Server",
            description=f"**Server:** {server.name}"
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(
            f"❌ API error: `{e}`"
        )


@bot.tree.command(name="command", description="Run an ER:LC server command")
@app_commands.describe(
    command="The ER:LC command to execute, for example :h Hello"
)
async def command(
    interaction: discord.Interaction,
    command: str
):

    await interaction.response.defer(ephemeral=True)

    try:
        result = await bot.erlc.command(command)

        await interaction.followup.send(
            f"✅ Command sent.\n```{result}```"
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Command failed: `{e}`"
        )


bot.run(DISCORD_TOKEN)
