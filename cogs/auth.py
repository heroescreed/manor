import asyncio
import os
import random
import re
import smtplib
import string

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput

import ids


async def check_student_number(student_number: str) -> bool:
    print(f"Checking student number: {student_number}")
    if len(student_number) != 9:
        return False
    return bool(re.match(r"^\d{9}$", student_number))

class AuthModal(Modal, title="Verify your Student Status"):
    print("AuthModal called")
    name = TextInput(label="Please enter your name..", placeholder="As it appears on your student ID card. (e.g. Alan Turing)", required=True, max_length=128)
    student_id = TextInput(label="Please enter your student ID number.", placeholder="Full number please. (e.g. 123456789)", required=True, max_length=9)
    email = TextInput(label="Enter your university username.", placeholder="e.g. c1234567, a.turing, etc...", required=True, max_length=128)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        print("Modal Submitted")
        if not await check_student_number(self.student_id.value):
            print("Invalid student number, modal failed.")
            await interaction.response.send_message("We're very sorry, but your student number you entered is not valid.\nPlease check it and try again. If it still doesn't work, please open a ticket.", ephemeral=True)
            return

        verification_code = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        print("Generated verification code")
        try:
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = int(os.getenv("SMTP_PORT"))  # type: ignore
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            with smtplib.SMTP(smtp_server, smtp_port) as server:  # type: ignore
                server.starttls()
                server.login(smtp_username, smtp_password)  # type: ignore
                server.sendmail(smtp_username, f"{self.email.value}@ncl.ac.uk", f"Subject: NUCATS Discord Verification Code\n\nHello {self.name.value},\n\nThank you for starting your verification steps on the NUCATS Discord server.\n\nTo complete your verification, please type the following into the verification channel:\n\nNUCATS{self.student_id.value}{verification_code}\n\nPlease do not share this code with anyone else.\n\nIf you did not request this code, please ignore this email.\n\nThis inbox does accept emails, however replies to this email will be ignored and discarded.\nIf you have any questions, please create a ticket in the server.\n\nKind Regards,\n\nNUCATS Committee.")
                print(f"Sent verification email to {self.email.value}@ncl.ac.uk")
        except Exception as error:  # noqa: BLE001
            print(f"Error sending email: {error}")
            await interaction.response.send_message("We're very sorry, but we couldn't send you a verification email. Please create a ticket to be verified manually.", ephemeral=True)
            return

        await interaction.response.send_message("Thank you! We've sent a verification code to your university email. Please check your university email address.\n\nIf you can't find the code, check your spam folder, or try verifying again.", ephemeral=True)

        def check(message):
            return message.author == interaction.user and message.channel.id == ids.auth_channel and message.content.startswith(f"NUCATS{self.student_id.value}")

        try:
            message = await self.bot.wait_for("message", check=check, timeout=300.0)
            if message.content == f"NUCATS{self.student_id.value}{verification_code}":
                print(f"User {interaction.user} verified successfully.")
                await message.delete()
                await asyncio.sleep(1)
                await interaction.user.add_roles(discord.Object(id=ids.verified_role))
                await interaction.followup.send(f"Thank you {interaction.user.mention}! You have been verified. Please check your roles to ensure you have the 'Verified' role.", ephemeral=True)
            else:
                await interaction.followup.send("The verification code you entered is incorrect. Please try again.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Please try the verification process again.", ephemeral=True)


class AuthCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="auth", description="For users to verify themselves.")
    async def auth(self, ctx: commands.Context):
        if ctx.interaction is not None:
            await ctx.interaction.response.send_modal(AuthModal(self.bot))
            return
        await ctx.send("Please use /auth from Discord.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AuthCog(bot))
