import discord
from discord.ext import commands, tasks

from bot import Bot
from utils import is_committee_member
from views import Ticket_Open, reset_cooldown_loop

class SupportCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.reset_cooldown_list.start()

    @commands.hybrid_command(name="panel", description="Send the support pannel to the selected channel.")
    async def support(self, ctx: commands.Context, channel: discord.TextChannel):
        if not is_committee_member(ctx):
            await ctx.send("You do not have permission to use this command.", ephemeral=True)
            return
        
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("I could not find the channel.", ephemeral=True)
            return

        embed = discord.Embed(title="Open a ticket!", description="Open ticket to Verify or show evidence for Member/Free Member roles", color=discord.Colour.magenta())
        view = Ticket_Open(self.bot)
        await channel.send(embed=embed, view=view)
        await ctx.send("Support panel sent.", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.bot.add_view(Ticket_Open(self.bot))
            print("Loaded Ticket_Open view")
        except Exception as e:
            print(e)
            print("Failed to load Ticket_Open view")

    @tasks.loop(minutes=1)
    async def reset_cooldown_list(self):
        await self.bot.wait_until_ready()
        await reset_cooldown_loop()

async def setup(bot: Bot):
    await bot.add_cog(SupportCog(bot))