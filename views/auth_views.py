import discord, string, random, os, smtplib
from discord.ext import commands
from discord.ui import Button, Modal, TextInput, View

from utils import check_student_number
from constants import verified_role

class AuthModal(Modal, title="Verify your Student Status"):
    name = TextInput(label="Please enter your name..", placeholder="As it appears on your student ID card. (e.g. Alan Turing)", required=True, max_length=128)
    student_id = TextInput(label="Please enter your student ID number.", placeholder="Full number please. (e.g. 123456789)", required=True, max_length=9)

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        self.stop()


class VerificationModal(Modal, title="Enter your verification code"):
    verification_code_input = TextInput(
        label="Verification code",
        placeholder="Enter the 8-character code from your university email.",
        required=True,
        min_length=8,
        max_length=8
    )

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        self.stop()
        

class VerificationPromptView(View):
    def __init__(self, verification_code: str):
        super().__init__(timeout=300)
        self.verification_code = verification_code

    @discord.ui.button(label="Enter verification code", style=discord.ButtonStyle.primary)
    async def enter_code(self, interaction: discord.Interaction, button: Button):
        modal = VerificationModal()
        await interaction.response.send_modal(modal)

        await modal.wait()
        if not modal.verification_code_input.value:
            return
        
        if modal.verification_code_input.value != self.verification_code:
            await interaction.followup.send(
                "The verification code you entered is incorrect. Please try again.",
                ephemeral=True,
            )
            return

        role = interaction.guild.get_role(verified_role)
        if not role:
            await interaction.followup.send(
                "The 'Verified' role does not exist in this server. Please contact a comitte member.",
                ephemeral=True,
            )
            return
        
        await interaction.user.add_roles(role)

        await interaction.followup.send(
            f"Thank you {interaction.user.mention}! You have been verified. Please check your roles to ensure you have the 'Verified' role.",
            ephemeral=True)
        self.stop()

class AuthView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify yourself", style=discord.ButtonStyle.primary, custom_id="nucats:auth")
    async def auth_button(self, interaction: discord.Interaction, button: Button):
        auth_modal = AuthModal()
        await interaction.response.send_modal(auth_modal)
        await auth_modal.wait()
        if not auth_modal.name.value or not auth_modal.student_id.value:
            return

        # derive email from id
        email = "c" + auth_modal.student_id.value[1 : -1]
        print(f"Derived email: {email}")
        verification_code = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        print("Generated verification code")
        try:
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = int(os.getenv("SMTP_PORT"))  # type: ignore
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            if smtp_username is None or smtp_password is None:
                raise RuntimeError("SMTP credentials are not configured")
            with smtplib.SMTP(smtp_server, smtp_port) as server:  # type: ignore
                server.starttls()
                server.login(smtp_username, smtp_password)  # type: ignore
                server.sendmail(smtp_username, f"{email}@ncl.ac.uk", f"Subject: NUCATS Discord Verification Code\n\nHello {auth_modal.name.value},\n\nThank you for starting your verification steps on the NUCATS Discord server.\n\nTo complete your verification, enter the following code in the verification modal in Discord:\n\n{verification_code}\n\nPlease do not share this code with anyone else.\n\nIf you did not request this code, please ignore this email.\n\nThis inbox does accept emails, however replies to this email will be ignored and discarded.\nIf you have any questions, please create a ticket in the server.\n\nKind Regards,\n\nNUCATS Committee.")
                print(f"Sent verification email to {email}@ncl.ac.uk")
        except Exception as error:  # noqa: BLE001
            print(f"Error sending email: {error}")
            await interaction.response.send_message("We're very sorry, but we couldn't send you a verification email. Please create a ticket to be verified manually.", ephemeral=True)
            return

        verification_view = VerificationPromptView(verification_code)
        await interaction.followup.send("We've sent a verification code to your university email. Click the button below to enter it.", ephemeral=True, view=verification_view)