import random
import discord
from discord.ext import commands

from constants import welcome_channel



class MemberEventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(welcome_channel)
        await channel.send(f"Welcome {member.mention} to the NUCATS Discord server! Please read the rules and verify yourself using the authentication button in the auth channel.")  # type: ignore
        await channel.send(f"https://http.cat/{self.random_status_code()}")  # type: ignore

    @staticmethod
    def random_status_code() -> int:
        return random.choice([
            100, 101, 102, 200, 201, 202, 203, 204, 206, 207, 300, 301, 302, 303,
            304, 305, 307, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
            411, 412, 413, 414, 415, 416, 417, 418, 420, 421, 422, 423, 424, 425,
            426, 429, 431, 444, 450, 451, 497, 498, 499,
        ])


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberEventsCog(bot))
