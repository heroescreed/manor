import discord
from discord.ext import commands

from constants import verified_role, stage_1_role, stage_2_role, stage_3_role, alumni_role
from utils import is_committee_member

class CommitteeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #TODO: Turn this into a view with buttons for yes/no, and a timeout of 60 seconds. If the user does not respond in time, the command is cancelled.
    async def confirm(self, ctx: commands.Context) -> bool:
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ["yes", "no"]
        try:
            message = await self.bot.wait_for("message", check=check, timeout=60.0)
        except TimeoutError:
            return False
        return message.content.lower() == "yes"

    @commands.hybrid_command(name="verify", description="For committee members to verify a student.")
    async def verify(self, ctx: commands.Context, user: discord.Member):
        if not is_committee_member(ctx):
            print(f"User {ctx.author} attempted to use verify command without permission.")
            await ctx.send("You do not have permission to use this command.")
            return
        await user.add_roles(discord.Object(id=verified_role))
        await ctx.send(f"{user.mention} has been verified.")

    @commands.hybrid_command(name="unverify", description="For committee members to unverify a student.")
    async def unverify(self, ctx: commands.Context, user: discord.Member):
        if not is_committee_member(ctx):
            print(f"User {ctx.author} attempted to use unverify command without permission.")
            await ctx.send("You do not have permission to use this command.")
            return
        await user.remove_roles(discord.Object(id=verified_role))
        await ctx.send(f"{user.mention} has been unverified.")

    @commands.hybrid_command(name="unverify_all", description="For committee members to unverify all students.")
    async def unverify_all(self, ctx: commands.Context):
        if not is_committee_member(ctx):
            print(f"User {ctx.author} attempted to use unverify_all command without permission.")
            await ctx.send("You do not have permission to use this command.")
            return
        await ctx.send("Please take extreme caution when running this command. This command removes verification from all users in the server. Are you sure you want to continue? (yes/no)")
        if not await self.confirm(ctx):
            await ctx.send("Command cancelled.")
            return
        await ctx.send("Are you absolutely sure you want to UNVERIFY ALL USERS?\nThis action is not reversable without a few hours of work, blood, sweat, and tears.\nPlease make sure you are running the right command.\nYou are about to remove the 'Verified' role from everyone in the server.\nDo you DEFINITELY want to continue? (yes/no)")
        if not await self.confirm(ctx):
            await ctx.send("Command cancelled.")
            return
        await ctx.send("Okay. Unverifying all users now. This may take a few minutes.")
        for member in ctx.guild.members:  # type: ignore
            if verified_role in [role.id for role in member.roles]:
                print(f"Removing verified role from {member}.")
                await member.remove_roles(discord.Object(id=verified_role))
        await ctx.send("All users have been unverified.")

    # TODO: This command needs to be edited to ensure the users roles in "Channels and Roles" are also updated, otherwise it freaks out.
    @commands.hybrid_command(name="stage_up", description="Move all users in the server up a stage.")
    async def stage_up(self, ctx: commands.Context):
        if not is_committee_member(ctx):
            print(f"User {ctx.author} attempted to use stage_up command without permission.")
            await ctx.send("You do not have permission to use this command.")
            return
        await ctx.send("Are you sure you want to move all users up a stage? This action is reversable but annoying to do. (yes/no)")
        if not await self.confirm(ctx):
            await ctx.send("Command cancelled.")
            return
        await ctx.send("Moving all users up a stage now. This may take a few minutes.")
        for member in ctx.guild.members:  # type: ignore
            print(f"Editing roles for {member}.")
            role_ids = [role.id for role in member.roles]
            if stage_1_role in role_ids:
                await member.remove_roles(discord.Object(id=stage_1_role))
                await member.add_roles(discord.Object(id=stage_2_role))
            elif stage_2_role in role_ids:
                await member.remove_roles(discord.Object(id=stage_2_role))
                await member.add_roles(discord.Object(id=stage_3_role))
            elif stage_3_role in role_ids:
                await member.remove_roles(discord.Object(id=stage_3_role))
                await member.add_roles(discord.Object(id=alumni_role))
        await ctx.send("All users have been moved up a stage.\nPlease make an announcement to the server to inform members of this change.")

    @commands.hybrid_command(name="verify_all", description="For committee members to verify all students.")
    async def verify_all(self, ctx: commands.Context):
        """
        quite rare for this to be used, im only making this whilst locking down the server.
        this verifies EVERYONE below the nucats bot role, so be careful, youll probs verify a bot or two but easy to get rid of when they pop up.
        """
        if not is_committee_member(ctx):
            print(f"User {ctx.author} attempted to use verify_all command without permission.")
            await ctx.send("You do not have permission to use this command.")
            return
        await ctx.send("Are you sure you want to verify all users? This action is reversable but annoying to do. (yes/no)")
        if not await self.confirm(ctx):
            await ctx.send("Command cancelled.")
            return
        await ctx.send("Verifying all users now. This may take a few minutes.")
        for member in ctx.guild.members:  # type: ignore
            if verified_role not in [role.id for role in member.roles]:
                print(f"Adding verified role to {member}.")
                await member.add_roles(discord.Object(id=verified_role))
        await ctx.send("All users have been verified.")

async def setup(bot: commands.Bot):
    await bot.add_cog(CommitteeCog(bot))
