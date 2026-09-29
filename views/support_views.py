import discord, asyncio, io, time
from chat_exporter import chat_exporter

from bot.bot import Bot
from db import get_db, OpenTickets
from constants import TICKET_CATEGORY_ID, committee_role, COLOUR_MAIN, COLOUR_NEUTRAL, COLOUR_GOOD, ticket_log_channel

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

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        creation_cooldown.append(interaction.user.id)

        while not self.bot.is_ready():
            await asyncio.sleep(1)

        with get_db() as db:
            existing_ticket = db.query(OpenTickets).filter_by(user_id=interaction.user.id).first()
            if existing_ticket:
                existing_channel = self.bot.get_channel(existing_ticket.channel_id) # type: ignore
                if existing_channel:
                    await existing_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, view_channel=True, embed_links=True, attach_files=True) # type: ignore
                    await interaction.response.send_message(f"You already have an open ticket, use that one instead.\n\n{existing_channel.mention}", ephemeral=True) # type: ignore
                    creation_cooldown.remove(interaction.user.id)
                    return
                else:
                    db.delete(existing_ticket)
                    db.commit()

        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            creation_cooldown.remove(interaction.user.id)
            return

        category = await interaction.guild.fetch_channel(TICKET_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            category = None

        committee = interaction.guild.get_role(committee_role)
        if committee is None:
            await interaction.response.send_message("The committee role does not exist in this server. Please contact an administrator.", ephemeral=True)
            creation_cooldown.remove(interaction.user.id)
            return

        ticket = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            topic=f"Ticket for {interaction.user.name} ({interaction.user.id})",
            overwrites={
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True, manage_messages=True, send_messages=True, embed_links=True, attach_files=True),
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                committee: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True)
            }
        )

        embed = discord.Embed(title="Ticket Created", description=f"Your ticket has been created. Please wait for a committee member to assist you.", color=discord.Colour.blue())
        await ticket.send(content=f"{interaction.user.mention}{committee.mention}", embed=embed)



async def reset_cooldown_loop():
    global creation_cooldown
    creation_cooldown = []