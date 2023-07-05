import discord
import typing
import os

from discord.ext import commands

from views import views
from utils import utils

from dbmanager.dbmanager import DBManager
from dbmanager.models import OWAccount

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

#TODO: Move all tokens and psswords to env. variables
#DONE

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

db = DBManager(DB_USER, DB_PASS)

ticketEmbed = discord.Embed(title="Account request", description="If you want an account to start playing please click the button below to start a ticket. If you have been already given an account, a new one cannot be given")

@bot.event
async def on_ready():
    bot.add_view(views.TicketStarterView(db))
    bot.add_view(views.TicketDone(db))
    bot.add_view(views.PaymentConfirmation(db))
    await db.create_tables()

    print("Bot is connected and online") 

@bot.event
async def on_guild_join(guild: discord.Guild):

    adminPanelPermissions = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    ticketChannelPermission = {
        guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
        guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    admin_panel = discord.utils.get(guild.text_channels, name="admin-panel")

    if admin_panel is not None:
        print("Server already has channels, not creating new ones")
    else:
        adminCat = await guild.create_category(name="admin", overwrites=adminPanelPermissions)
        ticketCat = await guild.create_category(name="tickets")

        requestChannel = await guild.create_text_channel(name="account-request", category=ticketCat, overwrites=ticketChannelPermission)
        await requestChannel.send(embed=ticketEmbed, view=views.TicketStarterView(db))

        await guild.create_text_channel(name="admin-panel", overwrites=adminPanelPermissions, category=adminCat)

@bot.command()
async def done(ctx: commands.Context):

    if (ctx.channel == discord.utils.get(ctx.guild.text_channels, name="admin-panel")):
        FinishedAccountEmbed = discord.Embed(title="Finished Accounts")

        account: OWAccount

        finishedAccounts = await db.get_finished_accounts()

        if len(finishedAccounts) != 0:
            for account in finishedAccounts:
                FinishedAccountEmbed.add_field(name="", value=f"ID: {account.id}, E-mail: {account.email}", inline=False)
        else:
            FinishedAccountEmbed.add_field(name="", value="There is no any finished accounts currently", inline=False)

        FinishedAccountEmbed.add_field(name="More help..", value="To export full info, use the command !export [email]", inline=False)

        await ctx.send(embed=FinishedAccountEmbed)

@bot.command()
async def export(ctx: commands.Context, id: typing.Optional[int]):
    adminpanel = discord.utils.get(ctx.guild.text_channels, name="admin-panel")

    if (ctx.channel == adminpanel):
        if (id is None):
            await ctx.send("Please provide the id of the account to export")
            return
        else:
            account = await db.get_account(id)
            info = utils.export(account)
            await ctx.channel.send(info)

    elif ("account-for-" in ctx.channel.name and ctx.author == ctx.guild.owner):
        account = await db.get_account_by_channel(str(ctx.channel.id))

        #TODO: add the export feature
        #DONE
        info = utils.export(account)
        
        await ctx.message.delete()
        await adminpanel.send(f"{ctx.guild.owner.mention}\n" + info)


@bot.command()
async def schedule(ctx: commands.Context, id: typing.Optional[int], amount: typing.Optional[int], date: typing.Optional[str]):
    if (ctx.author == ctx.guild.owner):

        if ("account-for-" in ctx.channel.name):
            payment = await db.get_payment_by_id(id)

            await ctx.message.delete()
            await db.set_payment_info(id, date, amount)

            member = get_channel_member(ctx.channel)

            await ctx.send(f"{member.mention}\nAccount has been checked and payment has been scheduled for {date}")
        
        elif (ctx.channel.name == "admin-panel"):
            payments = await db.get_payments()

            scheduledPaymentsEmbed = discord.Embed(title="Scheduled payments")

            if len(payments) == 0:
                scheduledPaymentsEmbed.add_field(name="", value="No current payments registered")

            for payment in payments:
                date = payment.paymentDate

                if date is None:
                    date = "Unscheduled"

                scheduledPaymentsEmbed.add_field(name="", value=f"Process ID: {payment.id}, User: {payment.user}, Number: {payment.paymentNum}, Amount: {payment.amount}, Date: {date}, Paid: {payment.payed}, Confirmed: {payment.confirmed}", inline=False)

            await ctx.send(embed=scheduledPaymentsEmbed)

@bot.command()
async def paid(ctx: commands.Context, id: int):
    if (ctx.channel.name == "admin-panel"):
        currentPayment = await db.set_payment_done(id)
        AccountDoneEmbed = discord.Embed(title="Payment placed", description=f"Your scheduled paymen has been placed, please confirm your payment after receiving using the button below. You will be asked to write the amount received")
        
        payment = await db.get_payment_by_id(id)

        channel = discord.utils.get(ctx.guild.channels, id=int(payment.channelid))
        member = get_channel_member(channel)

        await channel.send(f"{member.mention}\n", embed=AccountDoneEmbed, view=views.PaymentConfirmation(db))
        await ctx.send(f"Payment for {currentPayment.user} is made, waiting for user's confirmation")

@bot.command()
async def find(ctx: commands.Context, id: int):
    if (ctx.channel.name == "admin-panel"):
        payment = await db.get_payment_by_id(id)

        channel = discord.utils.get(ctx.guild.channels, id=int(payment.channelid))
        await ctx.send(f"Channel associated with payment id {id}: {channel.mention}")

def get_channel_member(channel: discord.TextChannel):
    for member in channel.members:
        if (member != channel.guild.me and member != channel.guild.owner):
            return member


bot.run(TOKEN)