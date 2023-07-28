import discord

from dbmanager.dbmanager import DBManager
from dbmanager.models import Payment, OWAccount


class DoneForm(discord.ui.Modal):
    
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, default="Bronze 5 DPS", required=True, max_length=255)
    paymentNumber = discord.ui.TextInput(label="Cash Payment Number", style=discord.TextStyle.short, required=True, max_length=11)


    def __init__(self, dbManager: DBManager) -> None:
        super().__init__(title="Please fill the following")
        self.dbManager = dbManager

    async def on_submit(self, interaction: discord.Interaction):
        #TODO: Update database with cash payment number

        if (not self.paymentNumber.value.isdigit()):
            await interaction.response.send_message("Wrong phone number given please try again")
            return

        await self.dbManager.set_as_finished(interaction.user.name+interaction.user.discriminator, self.description.value)

        payment = Payment(user=interaction.user.name+interaction.user.discriminator, paymentNum=self.paymentNumber.value, channelid=str(interaction.channel_id))
        await self.dbManager.add(payment)

        await interaction.response.send_message(f"Account marked as done, Owner will check account and schedule payment, Process ID: {payment.id}") 

class ConfirmationForm(discord.ui.Modal):

    amount = discord.ui.TextInput(label="Amount Received" , style=discord.TextStyle.short, required=True, max_length=6)

    def __init__(self, dbManager: DBManager) -> None:
        super().__init__(title="Please write the amount received")
        self.dbManager = dbManager

    async def on_submit(self, interaction: discord.Interaction):
        admin_panel = discord.utils.get(interaction.guild.channels, name="admin-panel")

        payment = await self.dbManager.get_payment_by_channelid(str(interaction.channel_id))

        if (int(self.amount.value) == payment.amount):
            if (not payment.confirmed):    
                await self.dbManager.set_payment_confirmed(payment.id)
                await admin_panel.send(f"{interaction.guild.owner.mention}\n{interaction.user.name}'s payment was confirmed with the amount {payment.amount}")
                await interaction.response.send_message("Payment was confirmed succesfully")
            elif (payment.confirmed):
                await interaction.response.send_message("Payment has already been confirmed")

        else:
            await interaction.response.send_message("The amount given is not the same as the one sent, tha payment was not confirmed, please the check the amount received again or wait for the payment to be received if not yet.")

class TicketDone(discord.ui.View):

    def __init__(self, dbManager: DBManager) -> None:
        super().__init__(timeout=None)

        self.dbManager = dbManager

    @discord.ui.button(label="Done", style=discord.ButtonStyle.blurple, custom_id="done_button")
    async def accountDone(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (interaction.channel.name == f"account-for-{interaction.user.name+interaction.user.discriminator}"):
            await interaction.response.send_modal(DoneForm(self.dbManager))

class PaymentConfirmation(discord.ui.View):
    def __init__(self, dbManager: DBManager) -> None:
        super().__init__(timeout=None)

        self.dbManager = dbManager

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.blurple, custom_id="confirm_payment")
    async def accountDone(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (interaction.channel.name == f"account-for-{interaction.user.name+interaction.user.discriminator}"):
            await interaction.response.send_modal(ConfirmationForm(self.dbManager))


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
                label="Fresh Account",
                value="0",
                description="Fresh account to unlock competitive"
            ),
            discord.SelectOption(
                label="1 Role",
                value="1",
                description="Account for 1 role derank"
            ),
            discord.SelectOption(
                label="2 Role",
                value="2",
                description="Account for 1 role derank"
            ),
            discord.SelectOption(
                label="3 Role",
                value="3",
                description="Account for 1 role derank"
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

        if (self.bot.trusted_role not in interaction.user.roles):
            await interaction.response.send_message("You are not yet trusted, please DM the mods to get the roles and start playing :)", ephemeral=True)
            return
    
        #Check if the user has chosen an answer
        if (user_str not in self.answers.keys()):
            await interaction.response.send_message("Please select your account type first", ephemeral=True)
            return

        #Check if the user alreasy has an account
        userCheck = await self.dbManager.check_user(interaction.user.name+interaction.user.discriminator)

        if (not userCheck):
            await interaction.response.send_message("You already have an account requested, please finish it first", ephemeral=True)
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
        retrieved_acc : OWAccount = await self.dbManager.get_new_account(interaction.user.name+interaction.user.discriminator, account_type)


        if retrieved_acc is None:
            await interaction.response.send_message("There is no any account available currently, please try again soon", ephemeral=True)
            self.answers.pop(user_str)
            return

        #TODO: Add email password entry and change taken to true
        AccountReturnEmbed = discord.Embed(title="Account Information", description=f"E-mail: {retrieved_acc.email}\nBattle.net Password: {retrieved_acc.password}")
        AccountReturnEmbed.add_field(name="More Help..", value="After finishing the account click the Done button. You will be asked to write a description for what you did and your cash payment number, then the owner will check the account and schedule a payment\nIf any help needed you can write a message, the owner can see it", inline=False)

        ticket = await guild.create_text_channel(name=f"account-for-{interaction.user.name+interaction.user.discriminator}", overwrites=overwrites, reason=f"Account request for {interaction.user}", category=guild.get_channel(interaction.channel.category_id))
        await ticket.send(embed=AccountReturnEmbed, view=TicketDone(self.dbManager))

        await self.dbManager.set_channel(retrieved_acc.id, str(ticket.id))
        
        await interaction.response.send_message(f"Opened ticket at {ticket.mention}", ephemeral=True)
        
        self.bot.accounts["total"] -= 1
        self.bot.accounts[self.answers[user_str]] -= 1

        await self.bot.update_stock()