import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import ids


class NUCATSBot(commands.Bot):
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix="!", intents=intents)

    print("Loading extensions...")
    async def setup_hook(self):
        for extension in (
            "cogs.auth",
            "cogs.committee",
            "cogs.general",
            "cogs.member_events",
        ):
            print(f"Loading extension: {extension}")
            await self.load_extension(extension)
            print(f"Loaded extension: {extension}")

    
        self.tree.copy_global_to(guild=discord.Object(id=ids.server_id))
        await self.tree.sync(guild=discord.Object(id=ids.server_id))

print("Getting dotenv")
load_dotenv()
token = os.getenv("CLIENT_TOKEN")
print("Starting bot...")
intents = discord.Intents.all()

client = NUCATSBot(intents=intents)


@client.event
async def on_ready():
    print(f"Bot is ready. Logged in as {client.user}")

client.run(token)  # type: ignore
