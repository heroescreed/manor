import asyncio
import os
import random
import re
import smtplib
import string

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput
from dotenv import load_dotenv
from lightstreamer_client import LightstreamerClient, Subscription, SubscriptionListener
from uwuipy import Uwuipy

import ids


async def check_student_number(student_number: "str") -> "bool":
    """Checks if a given student number is valid

    :param student_number: String to be checked
    :return: True if valid, false if invalid
    """
    if len(student_number) != 9:
        return False
    return bool(re.match(r"^\d{9}$", student_number))

class AuthModal(Modal, title="Verify your Student Status"):
    """
    This class is a modal used to verify a user's student status.
    """
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
        if not await check_student_number(self.student_id.value):
            await interaction.response.send_message("We're very sorry, but your student number you entered is not valid.\nPlease check it and try again. If it still doesn't work, please open a ticket.", ephemeral=True)
            return

        # Create random verification code
        chars = string.ascii_letters + string.digits
        verification_code = ''.join(random.choice(chars) for _ in range(8))

        # Send email to user with verification code
        try:
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = int(os.getenv("SMTP_PORT")) # type: ignore
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")

            with smtplib.SMTP(smtp_server, smtp_port) as server: # type: ignore
                server.starttls()
                server.login(smtp_username, smtp_password) # type: ignore
                server.sendmail(
                    smtp_username, # type: ignore
                    f"{self.email.value}@ncl.ac.uk",
                    f"Subject: NUCATS Discord Verification Code\n\nHello {self.name.value},\n\nThank you for starting your verification steps on the NUCATS Discord server.\n\nTo complete your verification, please type the following into the verification channel:\n\nNUCATS{self.student_id.value}{verification_code}\n\nPlease do not share this code with anyone else.\n\nIf you did not request this code, please ignore this email.\n\nThis inbox does accept emails, however replies to this email will be ignored and discarded.\nIf you have any questions, please create a ticket in the server.\n\nKind Regards,\n\nNUCATS Committee."
                )
        except Exception as e: # noqa: BLE001
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
                await asyncio.sleep(1)
                await interaction.user.add_roles(discord.Object(id=ids.verified_role)) # type: ignore
                await interaction.followup.send(f"Thank you {interaction.user.mention}! You have been verified. Please check your roles to ensure you have the 'Verified' role.", ephemeral=True)
            else:
                await interaction.followup.send("The verification code you entered is incorrect. Please try again.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Please try the verification process again.", ephemeral=True)

# Gets application token
load_dotenv()
token = os.getenv("CLIENT_TOKEN")

uwu = Uwuipy()

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

@client.hybrid_command(name="coinflip", description="Flips a coin.")
async def coinflip(ctx):
    """Flips a coin and returns the result."""
    # pick heads or tails for user
    await ctx.send(f"Flipping coin, {ctx.author.mention}, reply with your call (heads or tails).")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["heads", "tails"]

    msg = await client.wait_for("message", check=check, timeout=60.0)
    if msg.content.lower() == "heads":
        call = "Heads"
    else:
        call = "Tails"

    await ctx.send(f"You called {call}. Flipping the coin now...")

    await asyncio.sleep(2)  # wait for dramatic effect

    result = random.choice(["Heads", "Tails"])
    await ctx.send(f"The coin landed on {result}.")

@client.hybrid_command(name="roll", description="Rolls a die.")
async def roll(ctx, sides: int = 6, rolls: int = 1):
    """Rolls a die and returns the result."""
    if sides < 1 or rolls < 1:
        await ctx.send("Please enter a valid number of sides and rolls.")
        return

    results = [random.randint(1, sides) for _ in range(rolls)]
    await ctx.send(f"You rolled: {', '.join(map(str, results))}")
    

@client.hybrid_command(name="httpcat", description="Return a random image from http.cat.")
async def httpcat(ctx):
    """Returns a random HTTP cat image."""
    status_codes = [100, 101, 102, 200, 201, 202, 203, 204, 206, 207, 300, 301, 302, 303, 304, 305, 307, 400, 401, 402,
                    403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 420,
                    421, 422, 423, 424, 425, 426, 429,
                    431,
                    444,
                    450,
                    451,
                    497,
                    498,
                    499,
                    ]
    status_code = random.choice(status_codes)
    await ctx.send(f"https://http.cat/{status_code}")

@client.hybrid_command(name="httpdog", description="Return a random image from http.dog.")
async def httpdog(ctx):
    """Returns a random HTTP dog image."""
    status_codes = [100, 101, 102, 200, 201, 202, 203, 204, 206, 207, 300, 301, 302, 303, 304, 305, 307, 400, 401, 402,
                        403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 420,
                        421, 422, 423, 424, 425, 426, 429,
                        431,
                        444,
                        450,
                        451,
                        497,
                        498,
                        499,
                        ]
    status_code = random.choice(status_codes)
    await ctx.send(f"https://http.dog/{status_code}.jpg")

@client.hybrid_command(name="credits", description="Shows the credits for the bot.")
async def credits(ctx):
    """Shows the credits for the bot."""
    await ctx.send("```\nBot originally developed by tinyTim567\nRewritten by Jack Eilles (amnexya) with assistance from NUCATS committee.\n```")

@client.hybrid_command(name="urandom", description="Returns a 256-byte string pulled from /dev/urandom")
async def urandom(ctx):
    """Returns a 256-byte string pulled from /dev/urandom."""
    random_bytes = os.urandom(256)  # 256 bytes = 2048 bits
    random_hex = random_bytes.hex()
    await ctx.send(f"Here is your 256-byte random string, freshly baked from /dev/urandom: ```\n{random_hex}\n```\nPlease don't actually use this as a secret key, everyone here has seen it.")

@client.hybrid_command(name="8ball", description="A magic 8-ball that can answer anything.")
async def eight_ball(ctx, *, question: str):
    """A magic 8-ball that can answer anything."""
    await ctx.send(f"Question: {question}")

    responses = [
        "Probably man.",
        "Idk, ask me later.",
        "Yes.", 
        "No.", 
        "Maybe.",
        "Think of this as Microsoft Authenticator, that's how bad the outlook is.",
        "You are asking a computer this, so the answer is probably no.",
        "Yes, but only if you are a cat.",
        "No, but only if you are a dog.",
        "Yes, but only if you are a human.",
        "No, but only if you are a robot.",
        "Yes, but only if you are a fish.",
        "No, but only if you are a bird.",
        "I'm sorry, but I cannot fulfill your request. As an AI language model, I am programmed to provide helpful and informative responses, but I cannot provide answers that are inappropriate or offensive. Please ask a different question.",
        "Sure",
        "Nope",
        "Absolutely",
        "Definitely not",
        "I guess?", 
        "Outlook hazy, try again later.", 
        "Yes, in due time.",
        "boneless chicken",
        "Not sure about that one.",
    ]

    # use the question as a seed for the rng but add a bit of noise too
    question += str(random.randint(1, 100))
    random.seed(question)
    response = random.choice(responses)
    await ctx.send(f"{response}")

@client.hybrid_command(name="bucket", description="This, is a bucket.")
async def bucket(ctx):
    """This, is a bucket."""
    await ctx.send("https://tenor.com/view/team-fortress-2-tf2-tf2-memes-gif-12176472853573905724")

@client.hybrid_command(name="uwu", description="Uwuifies your text.")
async def uwuify(ctx, text: str | None = None):
    """Uwuifies the last message sent in the channel, or the message you provide as an argument."""

    if text is None:
        # Get the last message sent in the channel
        async for message in ctx.channel.history(limit=2):
            if message.author != ctx.author:
                text = message.content
                break

    uwuified_text = uwu.uwuify(text)
    await ctx.send(uwuified_text)

@client.hybrid_command(name="rate", description="Rates something from 1 to 10.")
async def rate(ctx, item: str):
    """Rates the specified item from 1 to 10."""

    # Generate a random rating between 1 and 10
    rating = random.randint(1, 10)
    await ctx.send(f"{item} is rated {rating}/10.")

@client.hybrid_command(name="request_command", description="Ask the developers to add a new command.")
async def request_command(ctx, description: str):
    """Requests that the developers add a new command."""

    await ctx.send("Thanks! This has been sent to the committee for review. If they like it, it will be added.")
    await client.get_channel(ids.committee_channel).send(f"New command request from {ctx.author.mention}:\n{description}")

@client.event
async def on_member_join(member):
    """Sends a welcome message to the welcome channel when a user joins the server."""
    channel = client.get_channel(ids.welcome_channel)
    await channel.send(f"Welcome {member.mention} to the NUCATS Discord server! Please read the rules and verify yourself using /auth.") # type: ignore
    await httpcat(channel)  # type: ignore # Send a random http.cat image to the welcome channel

client.run(token) # type: ignore

