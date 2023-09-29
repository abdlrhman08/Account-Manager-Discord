import discord
import asyncio

import messages

from utils import utils

from dbmanager.dbmanager import DBManager
from dbmanager.models import Payment


class DoneForm(discord.ui.Modal):
    
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=True, max_length=255)
    paymentNumber = discord.ui.TextInput(label="Cash Payment Number", style=discord.TextStyle.short, required=True, max_length=11)
    paymentNumberConfirmation = discord.ui.TextInput(label="Cash Payment Number", style=discord.TextStyle.short, required=True, max_length=11)


    def __init__(self, dbManager: DBManager, type: int, bot) -> None:
        super().__init__(title="Please fill the following")
        self.dbManager = dbManager
        self.bot = bot

        if (type < 10):
            self.remove_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if (not self.paymentNumber.value.isdigit()):
            raise ValueError("Invalid input type")
        
        if (self.paymentNumber.value != self.paymentNumberConfirmation.value):
            raise ValueError("The payment numbers don't match, please try again")    

        await self.dbManager.set_as_finished(interaction.user.name+interaction.user.discriminator, self.description.value)

        payment = Payment(user=interaction.user.name+interaction.user.discriminator, paymentNum=self.paymentNumber.value, channelid=str(interaction.channel_id))
        await self.dbManager.add(payment)

        await interaction.followup.send(f"Account marked as done, Owner will check account and schedule payment, Process ID: {payment.id}") 
        await interaction.channel.edit(category=self.bot.finished_cat)
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        if (isinstance(error, ValueError)):
            await interaction.response.send_message(error, ephemeral=True)

class ConfirmationForm(discord.ui.Modal):

    amount = discord.ui.TextInput(label="Amount Received" , style=discord.TextStyle.short, required=True, max_length=6)

    def __init__(self, dbManager: DBManager, bot) -> None:
        super().__init__(title="Please write the amount received")
        self.dbManager = dbManager
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel_id = str(interaction.channel.id)

        payment = await self.dbManager.get_payment_by_channelid(channel_id)
        account_id = await self.dbManager.get_account_id_by_channel(channel_id)

        DMEmbed = discord.Embed(title="Ticket Confirmation \U00002705")
        DMEmbed.add_field(name="Account Identifier", value=account_id)
        DMEmbed.add_field(name="Info", value="Ticket was closed because payment confirmed")

        if (not self.amount.value.isdigit()):
            await interaction.followup.send("Invalid input given, please try again", ephemeral=True)
            return

        if (int(self.amount.value) != payment.amount):
            await interaction.followup.send(messages.MESSAGES["PAYMENT"])
            return
        
        if (not payment.confirmed):    
            await self.dbManager.set_payment_confirmed(payment.id)
            await self.bot.admin_panel.send(f"{self.bot.manager_role.mention}\n{interaction.user.name}'s payment was confirmed with the amount {payment.amount}")
            await interaction.followup.send("Payment was confirmed succesfully, closing ticket")
            await asyncio.sleep(3)
            await interaction.channel.set_permissions(utils.get_channel_member(interaction.channel), view_channel=False)
            await interaction.channel.edit(category=self.bot.paid_cat)
            await interaction.user.send(embed=DMEmbed)
        elif (payment.confirmed):
            await interaction.followup.send("Payment has already been confirmed")


class TicketDone(discord.ui.View):

    def __init__(self, dbManager: DBManager, bot) -> None:
        super().__init__(timeout=None)

        self.dbManager = dbManager
        self.bot = bot

    @discord.ui.button(label="Done", style=discord.ButtonStyle.blurple, custom_id="done_button")
    async def accountDone(self, interaction: discord.Interaction, button: discord.ui.Button):
        last_message = [message async for message in interaction.channel.history(limit=1)][0]
    
        if (not last_message.attachments):
            await interaction.response.send_message("Please upload all the screenshots first", ephemeral=True)
            return
        
        type: int
        try:
            type = await self.dbManager.get_account_type_by_channel(str(interaction.channel.id))
        except:
            await interaction.response.send_message("Experienced connectivity issues, Please try again now", ephemeral=True)
        else:
            Form = DoneForm(self.dbManager, type, self.bot)
            await interaction.response.send_modal(Form)
            await Form.wait()

            button.disabled = True

            await interaction.edit_original_response(view=self)
            
class PaymentConfirmation(discord.ui.View):
    def __init__(self, dbManager: DBManager, bot) -> None:
        super().__init__(timeout=None)

        self.dbManager = dbManager
        self.bot = bot

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.blurple, custom_id="confirm_payment")
    async def accountDone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfirmationForm(self.dbManager, self.bot))


'''Sub-type selector view'''
class SubtypeSelectorView(discord.ui.View):
    def __init__(self, main_type: int, dbManager: DBManager, bot) -> None:
        super().__init__()
        self.dbManager = dbManager
        self.bot = bot
        
        self.main_type = main_type
        self.account_type = main_type * 10

        utils.populate_options(bot.accounts, self.children[0], main_type)

        if (main_type == 3):
            self.remove_item(self.children[0])
    
    @discord.ui.select(
        custom_id="subtype_select",
        placeholder = "Choose a account type",
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select): # the function called when the user is done selecting options
        self.account_type += int(select.values[0])

        await interaction.response.defer()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.blurple, custom_id="ticket_button")
    async def initTicket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if (not (await self.dbManager.check_availability(self.account_type, True))):
            await interaction.followup.send(messages.MESSAGES["NO_ACCOUNTS"], ephemeral=True)
            self.stop()
            return
        
                #TODO: Put overwrites in their own place
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),

            #TODO: add owner permision and role permission
            interaction.guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            self.bot.manager_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            
        }

        id, type, email, password, battle_tag = await self.dbManager.get_new_account(interaction.user.name+interaction.user.discriminator, self.account_type)

        if (type < 10):
            goal = "Get this account to 50 Wins QP"
        else:
            goal = f"Derank {int(type / 10)} Role/s on this account to bronze"

        #TODO: Add email password entry and change taken to true
        AccountReturnEmbed = discord.Embed(title="Account Information", description=f"E-mail: {email}\nBattle.net Password: {password}\nBattle-tag: {battle_tag}")
        AccountReturnEmbed.add_field(name="What you should do", value=goal, inline=False)
        AccountReturnEmbed.add_field(name="More Help..", value=messages.MESSAGES["TICKET_HELP"], inline=False)

        ticket = await interaction.guild.create_text_channel(name=f"account-for-{interaction.user.name+interaction.user.discriminator}-{id}", overwrites=overwrites, reason=f"Account request for {interaction.user}", category=interaction.guild.get_channel(interaction.channel.category_id))
        await ticket.send(embed=AccountReturnEmbed, view=TicketDone(self.dbManager, self.bot))

        await self.dbManager.set_channel(id, str(ticket.id))

        #Update the total accounts available stock
        self.bot.accounts["total"] -= 1
        if (self.account_type != 30):
            self.bot.accounts[f"{self.main_type}Total"] -= 1
        self.bot.accounts[str(self.account_type)] -= 1
        
        await self.bot.update_stock()
        await interaction.edit_original_response(content=f"Opened ticket at {ticket.mention}", view=None)
        self.stop()

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
        await interaction.response.defer()
        msg = "Please select subtype: "
        
        if (self.bot.trusted_role not in interaction.user.roles and self.bot.manager_role not in interaction.user.roles):
            await interaction.followup.send(messages.MESSAGES["TRUSTED"], ephemeral=True)
            return
        
        if (await self.dbManager.check_user(interaction.user.name+interaction.user.discriminator)):
            await interaction.followup.send(messages.MESSAGES["REQUESTED"], ephemeral=True)
            return
        
        if (not (await self.dbManager.check_availability(int(select.values[0])))):
            await interaction.followup.send(messages.MESSAGES["NO_ACCOUNTS"], ephemeral=True)
            return
        
        if (select.values[0] == "3"):
            msg = "Please confirm"

        SubSelector = SubtypeSelectorView(int(select.values[0]), self.dbManager, self.bot)
        await interaction.followup.send(msg, view=SubSelector, ephemeral=True)

    
    '''   
    @discord.ui.button(label="Request an account", style=discord.ButtonStyle.blurple, custom_id="ticket_button")
    async def initTicket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        user_str = str(interaction.user)

        if (self.bot.trusted_role not in interaction.user.roles and self.bot.manager_role not in interaction.user.roles):
            await interaction.followup.send(messages.MESSAGES["TRUSTED"], ephemeral=True)
            return
        
        if (user_str not in self.answers.keys()):
            await interaction.followup.send("Please select your account type first", ephemeral=True)
            return

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

        '''