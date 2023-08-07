import discord
import asyncio

import messages

from utils import utils

from dbmanager.dbmanager import DBManager
from dbmanager.models import Payment, OWAccount


class DoneForm(discord.ui.Modal):
    
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, default="Bronze 5 DPS", required=True, max_length=255)
    paymentNumber = discord.ui.TextInput(label="Cash Payment Number", style=discord.TextStyle.short, required=True, max_length=11)


    def __init__(self, dbManager: DBManager, bot) -> None:
        super().__init__(title="Please fill the following")
        self.dbManager = dbManager
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        #TODO: Update database with cash payment number

        if (not self.paymentNumber.value.isdigit()):
            await interaction.response.send_message("Wrong phone number given please try again")
            return

        await self.dbManager.set_as_finished(interaction.user.name+interaction.user.discriminator, self.description.value)

        payment = Payment(user=interaction.user.name+interaction.user.discriminator, paymentNum=self.paymentNumber.value, channelid=str(interaction.channel_id))
        await self.dbManager.add(payment)

        await interaction.response.send_message(f"Account marked as done, Owner will check account and schedule payment, Process ID: {payment.id}") 
        await interaction.channel.edit(category=self.bot.finished_cat)

class ConfirmationForm(discord.ui.Modal):

    amount = discord.ui.TextInput(label="Amount Received" , style=discord.TextStyle.short, required=True, max_length=6)

    def __init__(self, dbManager: DBManager, bot) -> None:
        super().__init__(title="Please write the amount received")
        self.dbManager = dbManager
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        admin_panel = discord.utils.get(interaction.guild.channels, name="admin-panel")

        payment = await self.dbManager.get_payment_by_channelid(str(interaction.channel_id))

        DMEmbed = discord.Embed(title="Ticket Confirmation")
        DMEmbed.add_field(name="Account Identifier", value=interaction.channel.id)
        DMEmbed.add_field(name="Info", value="Ticket was closed because payment confirmed")

        if (int(self.amount.value) == payment.amount):
            if (not payment.confirmed):    
                await self.dbManager.set_payment_confirmed(payment.id)
                await admin_panel.send(f"{self.bot.manager_role.mention}\n{interaction.user.name}'s payment was confirmed with the amount {payment.amount}")
                await interaction.followup.send("Payment was confirmed succesfully, closing ticket")
                await asyncio.sleep(3)
                await interaction.channel.set_permissions(utils.get_channel_member(interaction.channel), view_channel=False)
                await interaction.channel.edit(category=self.bot.paid_cat)
                await interaction.user.send(embed=DMEmbed)
            elif (payment.confirmed):
                await interaction.followup.send("Payment has already been confirmed")

        else:
            await interaction.followup.send(messages.MESSAGES["PAYMENT"])

class TicketDone(discord.ui.View):

    def __init__(self, dbManager: DBManager, bot) -> None:
        super().__init__(timeout=None)

        self.dbManager = dbManager
        self.bot = bot

    @discord.ui.button(label="Done", style=discord.ButtonStyle.blurple, custom_id="done_button")
    async def accountDone(self, interaction: discord.Interaction, button: discord.ui.Button):
        last_message = [message async for message in interaction.channel.history(limit=1)][0]

        if (last_message.attachments):
            await interaction.response.send_modal(DoneForm(self.dbManager, self.bot))
            print(last_message.attachments[0].content_type)
        else:
            await interaction.response.send_message("Please upload all the screenshots first", ephemeral=True)

class PaymentConfirmation(discord.ui.View):
    def __init__(self, dbManager: DBManager, bot) -> None:
        super().__init__(timeout=None)

        self.dbManager = dbManager
        self.bot = bot

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.blurple, custom_id="confirm_payment")
    async def accountDone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfirmationForm(self.dbManager, self.bot))


class TicketStarterView(discord.ui.View):
    answers: dict = dict()

    def __init__(self, dbManager: DBManager, bot) -> None:
        super().__init__(timeout=None)

        self.dbManager = dbManager
        self.bot = bot

    @discord.ui.select(
        custom_id="type_select",
        placeholder = "Choose a account type",
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
        options = [
            discord.SelectOption(
                label="50 Wins",
                value="0",
                description="Get this account to 50 Wins QP"
            ),
            discord.SelectOption(
                label="1 Role",
                value="1",
                description="Get one role to bronze on this account"
            ),
            discord.SelectOption(
                label="2 Role",
                value="2",
                description="Get two roles to bronze on this account"
            ),
            discord.SelectOption(
                label="3 Role",
                value="3",
                description="Get three roles to bronze on this account"
            )
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select): # the function called when the user is done selecting options
        self.answers[str(interaction.user)] = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.button(label="Request an account", style=discord.ButtonStyle.blurple, custom_id="ticket_button")
    async def initTicket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        user_str = str(interaction.user)
        await interaction.response.defer()

        if (self.bot.trusted_role not in interaction.user.roles and self.bot.manager_role not in interaction.user.roles):
            await interaction.followup.send(messages.MESSAGES["TRUSTED"], ephemeral=True)
            return
    
        #Check if the user has chosen an answer
        if (user_str not in self.answers.keys()):
            await interaction.followup.send("Please select your account type first", ephemeral=True)
            return

        #Check if the user alreasy has an account
        userCheck = await self.dbManager.check_user(interaction.user.name+interaction.user.discriminator)

        if (not userCheck):
            await interaction.followup.send(messages.MESSAGES["REQUESTED"], ephemeral=True)
            self.answers.pop(user_str)
            return
        
        #TODO: Put overwrites in their own place
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),

            #TODO: add owner permision and role permission
            guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            self.bot.manager_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            
        }

        account_type = int(self.answers[user_str])
        id, type, email, password, battle_tag = await self.dbManager.get_new_account(interaction.user.name+interaction.user.discriminator, account_type)

        if email is None:
            await interaction.followup.send(messages.MESSAGES["NO_ACCOUNTS"], ephemeral=True)
            self.answers.pop(user_str)
            return

        goal: str = None

        if (type == 0):
            goal = "Get this account to 50 Wins QP"
        else:
            goal = f"Derank {type} Role/s on this account to bronze"

        #TODO: Add email password entry and change taken to true
        AccountReturnEmbed = discord.Embed(title="Account Information", description=f"E-mail: {email}\nBattle.net Password: {password}\nBattle-tag: {battle_tag}")
        AccountReturnEmbed.add_field(name="What you should do", value=goal, inline=False)
        AccountReturnEmbed.add_field(name="More Help..", value=messages.MESSAGES["TICKET_HELP"], inline=False)

        ticket = await guild.create_text_channel(name=f"account-for-{interaction.user.name+interaction.user.discriminator}-{id}", overwrites=overwrites, reason=f"Account request for {interaction.user}", category=guild.get_channel(interaction.channel.category_id))
        await ticket.send(embed=AccountReturnEmbed, view=TicketDone(self.dbManager, self.bot))

        await self.dbManager.set_channel(id, str(ticket.id))
        
        await interaction.followup.send(f"Opened ticket at {ticket.mention}", ephemeral=True)
        
        self.bot.accounts["total"] -= 1
        self.bot.accounts[self.answers[user_str]] -= 1

        self.answers.pop(user_str)

        await self.bot.update_stock()