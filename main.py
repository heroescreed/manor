import asyncio
from dotenv import load_dotenv
import os
import smtplib
import string
import random

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput

import ids
import tools

class AuthModal(Modal, title="Verify your Student Status"):
    name = TextInput(
        label="Please enter your name..",
        placeholder="As it appears on your student ID card. (e.g. Alan Turing)",
        required=True,
        max_length=128
    )

    student_id = TextInput(
        label="Please enter your student ID number.",
        placeholder="Full number please. (e.g. 123456789)",
        required=True,
        max_length=9
    )

    email = TextInput(
        label="Enter your university username.",
        placeholder="e.g. c1234567, a.turing, etc...",
        required=True,
        max_length=128
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Check if their ID is valid
        if not await tools.check_student_number(self.student_id.value):
            await interaction.response.send_message("We're very sorry, but your student number you entered is not valid.\nPlease check it and try again. If it still doesn't work, please open a ticket.", ephemeral=True)
            return

        # Create random verification code
        chars = string.ascii_letters + string.digits
        verification_code = ''.join(random.choice(chars) for _ in range(8))

        # Send email to user with verification code
        try:
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = int(os.getenv("SMTP_PORT"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(
                    smtp_username,
                    f"{self.email.value}@ncl.ac.uk",
                    f"Subject: NUCATS Discord Verification Code\n\nHello {self.name.value},\n\nThank you for starting your verification steps on the NUCATS Discord server.\n\nTo complete your verification, please type the following into the verification channel:\n\nNUCATS{self.student_id.value}{verification_code}\n\nPlease do not share this code with anyone else.\n\nIf you did not request this code, please ignore this email.\n\nThis inbox does accept emails, however replies to this email will be ignored and discarded.\nIf you have any questions, please create a ticket in the server.\n\nKind Regards,\n\nNUCATS Committee."
                )
        except Exception as e:
            print(f"Error sending email: {e}")
            await interaction.response.send_message("We're very sorry, but we couldn't send you a verification email. Please create a ticket to be verified manually.", ephemeral=True)
            return

        await interaction.response.send_message("Thank you! We've sent a verification code to your university email. Please check your university email address.\n\nIf you can't find the code, check your spam folder, or try verifying again.", ephemeral=True)

        # Wait for the user to send the requested message in the verification channel
        def check(m):
            return m.author == interaction.user and m.channel.id == ids.auth_channel and m.content.startswith(f"NUCATS{self.student_id.value}")

        try:
            msg = await client.wait_for("message", check=check, timeout=300.0)
            if msg.content == f"NUCATS{self.student_id.value}{verification_code}":
                await msg.delete()
                await interaction.user.add_roles(discord.Object(id=ids.verified_role))
                await interaction.followup.send(f"Thank you {interaction.user.mention}! You have been verified. Please check your roles to ensure you have the 'Verified' role.", ephemeral=True)
            else:
                await interaction.followup.send("The verification code you entered is incorrect. Please try again.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Please try the verification process again.", ephemeral=True)

# Gets application token
load_dotenv()
token = os.getenv("CLIENT_TOKEN")

class NUCATSBot(commands.Bot):
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=discord.Object(id=ids.server_id))
        await self.tree.sync(guild=discord.Object(id=ids.server_id))

intents = discord.Intents.all()
client = NUCATSBot(intents=intents)

@client.event
async def on_ready():
    print(f'Bot is ready. Logged in as {client.user}.')

@client.hybrid_command(name="ping", description="Check the bot's latency.")
async def ping(ctx):
    await ctx.send(f'Pong! Latency: {round(client.latency * 1000)} ms')

@client.hybrid_command(name="verify", description="For committee members to verify a student.")
async def verify(ctx, user: discord.Member):
    """
    Only people with the role ids.committee_role can use this command.
    This command upgrades a users role to ids.verified_role.
    Command should be invoked after a user has submitted a ticket with proof of membership.
    Command takes a user as an argument in the command itself.
    """

    if ids.committee_role not in [role.id for role in ctx.author.roles]:
        await ctx.send("You do not have permission to use this command.")
        return

    await user.add_roles(discord.Object(id=ids.verified_role))
    await ctx.send(f"{user.mention} has been verified.")

@client.hybrid_command(name="unverify", description="For committee members to unverify a student.")
async def unverify(ctx, user: discord.Member):
    """
    Only people with the role ids.committee_role can use this command.
    This command removes a user's verified role.
    Command takes a user as an argument in the command itself.
    """

    if ids.committee_role not in [role.id for role in ctx.author.roles]:
        await ctx.send("You do not have permission to use this command.")
        return

    await user.remove_roles(discord.Object(id=ids.verified_role))
    await ctx.send(f"{user.mention} has been unverified.")

@client.hybrid_command(name="unverify_all", description="For committee members to unverify all students.")
async def unverify_all(ctx):
    """
    Only people with the role ids.committee_role can use this command.
    This command removes the verified role from all users.
    Please take extreme caution when using this command.
    This command has not been fully tested due to the irreversable damage it can cause.
    It has only been tested up to the final warning.
    If it doesn't work when needed, you need to fix it. 
    Abandon all hope, ye who enter here.
    """

    if ids.committee_role not in [role.id for role in ctx.author.roles]:
        await ctx.send("You do not have permission to use this command.")
        return

    await ctx.send("Please take extreme caution when running this command. This command removes verification from all users in the server. Are you sure you want to continue? (yes/no)")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

    msg = await client.wait_for("message", check=check, timeout=60.0)
    if msg.content.lower() == "no":
        await ctx.send("Command cancelled.")
        return

    await ctx.send("""Are you absolutely sure you want to UNVERIFY ALL USERS? 
    This action is not reversable without a few hours of work, blood, sweat, and tears. 
    Please make sure you are running the right command. 
    You are about to remove the 'Verified' role from everyone in the server. 
    Do you DEFINITELY want to continue? (yes/no)
    """)

    msg = await client.wait_for("message", check=check, timeout=60.0)
    if msg.content.lower() == "no":
        await ctx.send("Command cancelled.")
        return

    await ctx.send("Okay. Unverifying all users now. This may take a few minutes.")

    for member in ctx.guild.members:
        if ids.verified_role in [role.id for role in member.roles]:
            await member.remove_roles(discord.Object(id=ids.verified_role))

    await ctx.send("All users have been unverified.")

@client.hybrid_command(name="auth", description="For users to verify themselves.")
async def auth(ctx):
    """
    This command is used in place of /verify, which is for manual verification.
    Users can use this command to verify themselves as Newcastle University students.
    This command takes no arguments, and will run with a modal.
    """
    if hasattr(ctx, "interaction") and ctx.interaction is not None:
        modal = AuthModal()
        await ctx.interaction.response.send_modal(modal)
        
        return

    # fallback if it was invoked as a normal command
    await ctx.send("Please use /auth from Discord.")

@client.hybrid_command(name="stage_up", description="Move all users in the server up a stage.")
async def stage_up(ctx):
    """Only people with the role ids.committee_role can run this command.
    This command is used at the start of a new academic year to move all users in the server up one stage.
    Stage 1 moves to 2, 2 to 3, 3 to alumni, etc...

    Args:
        ctx (_type_): Command Context
    """

    if ids.committee_role not in [role.id for role in ctx.author.roles]:
        await ctx.send("You do not have permission to use this command.")
        return

    await ctx.send("Are you sure you want to move all users up a stage? This action is reversable but annoying to do. (yes/no)")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

    msg = await client.wait_for("message", check=check, timeout=60.0)
    if msg.content.lower() == "no":
        await ctx.send("Command cancelled.")
        return

    await ctx.send("Moving all users up a stage now. This may take a few minutes.")

    for member in ctx.guild.members:
        if ids.stage_1_role in [role.id for role in member.roles]:
            await member.remove_roles(discord.Object(id=ids.stage_1_role))
            await member.add_roles(discord.Object(id=ids.stage_2_role))
        elif ids.stage_2_role in [role.id for role in member.roles]:
            await member.remove_roles(discord.Object(id=ids.stage_2_role))
            await member.add_roles(discord.Object(id=ids.stage_3_role))
        elif ids.stage_3_role in [role.id for role in member.roles]:
            await member.remove_roles(discord.Object(id=ids.stage_3_role))
            await member.add_roles(discord.Object(id=ids.alumni_role))

    await ctx.send("All users have been moved up a stage.\nPlease make an announcement to the server to inform members of this change.")

client.run(token)

