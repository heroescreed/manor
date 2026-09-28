import discord

from bot.bot import Bot

creation_cooldown = []

class Ticket_Open(discord.ui.View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="nucats:open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in creation_cooldown:
            await interaction.response.send_message("You are on cooldown for creating tickets. Please wait a few minutes before trying again.", ephemeral=True)
            return

        creation_cooldown.append(interaction.user.id)
        await interaction.response.defer(ephemeral=True, thinking=True)


async def reset_cooldown_loop():
    global creation_cooldown
    creation_cooldown = []