import discord
import typing

from discord.ext.commands.context import Context
import messages
import base64

from discord.ext import commands
from pyotp import totp

from dbmanager.models import OWAccount, Payment 
from utils import utils
from views import views


class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


        #b32code = base64.b32encode(bytes.fromhex("78406711dad5aa1b91ffc4f7c188f1468cc159f3")).decode()
        #self.handler = totp.TOTP(b32code, 8)

    @commands.command()
    async def done(self, ctx: commands.Context):
        if (self.__inadminpanel(ctx)):   
            FinishedAccountEmbed = discord.Embed(title="Finished Accounts")

            account: OWAccount
            finishedAccounts = await self.bot.db.get_finished_accounts()

            if len(finishedAccounts) != 0:
                for account in finishedAccounts:
                    channel = discord.utils.get(ctx.guild.channels, id=int(account.channelid))
                    FinishedAccountEmbed.add_field(name="", value=f"ID: {account.id}, E-mail: {account.email}, Channel: {channel.mention}", inline=False)
            else:
                FinishedAccountEmbed.add_field(name="", value="There is no any finished accounts currently", inline=False)

            FinishedAccountEmbed.add_field(name="More help..", value="To export full info, use the command !export [id]", inline=False)

            await ctx.send(embed=FinishedAccountEmbed)
    
    @commands.command()
    async def export(self, ctx: commands.Context, id: typing.Optional[int]):
        if (self.__inadminpanel(ctx)):
            if (id is None):
                await ctx.send("Please provide the id of the account to export")
                return
            else:
                account = await self.bot.db.get_account(id)
                info = utils.export(account)
                await ctx.channel.send(info)

        elif ("account-for-" in ctx.channel.name and utils.is_admin(self.bot, ctx)):
            account = await self.bot.db.get_account_by_channel(str(ctx.channel.id))

            #TODO: add the export feature
            #DONE
            info = utils.export(account)
            
            await ctx.message.delete()
            await self.bot.admin_panel.send(f"{ctx.author.mention}\n" + info)

    @commands.command()
    async def schedule(self, ctx: commands.Context, id: typing.Optional[int], amount: typing.Optional[int], date: typing.Optional[str]):
        if (utils.is_admin(self.bot, ctx)):

            if (utils.in_ticket(ctx)):
                payment = await self.bot.db.get_payment_by_id(id)

                await ctx.message.delete()
                await self.bot.db.set_payment_info(id, date, amount)

                member = utils.get_channel_member(ctx.channel)

                await ctx.send(f"{member.mention}\nAccount has been checked and payment has been scheduled for {date}")
            
            elif (self.__inadminpanel(ctx)):
                payments = await self.bot.db.get_payments_unconfirmed()

                scheduledPaymentsEmbed = discord.Embed(title="Upcoming Scheduled payments")

                if len(payments) == 0:
                    scheduledPaymentsEmbed.add_field(name="", value="No current upcoming payments registered")

                payment: Payment
                for payment in payments:
                    date = payment.paymentDate

                    if date is None:
                        date = "Unscheduled"

                    scheduledPaymentsEmbed.add_field(name="", value=f"Process ID: {payment.id}, User: {payment.user}, Number: {payment.paymentNum}, Amount: {payment.amount}, Date: {date}, Paid: {payment.payed}, Confirmed: {payment.confirmed}", inline=False)

                await ctx.send(embed=scheduledPaymentsEmbed)

    @commands.command()
    async def accounts(self, ctx: commands.Context):
        if (self.__inadminpanel(ctx)):
            accounts = await self.bot.db.get_accounts()

            AccountsEmbed = discord.Embed(title="Current accounts on database")

            if len(accounts) == 0:
                AccountsEmbed.add_field(name="", value="No current payments registered")

            account: OWAccount
            for account in accounts:
                AccountsEmbed.add_field(name="", value=f"Account ID: {account.id} E-Mail: {account.email}, User: {account.user}, Finished: {account.finished}", inline=False)

            await ctx.send(embed=AccountsEmbed)
                

    @commands.command()
    @commands.has_any_role("Manager")
    async def paid(self, ctx: commands.Context, id: typing.Optional[int]):
        AccountDoneEmbed = discord.Embed(title="Payment placed", description=messages.MESSAGES["PLACED_PAYMENT"])
        AccountDoneEmbed.add_field(name="Payed by", value=ctx.author.mention)

        if (self.__inadminpanel(ctx)):
            currentPayment : Payment = await self.bot.db.set_payment_done(id)
            
            payment = await self.bot.db.get_payment_by_id(id)

            channel = discord.utils.get(ctx.guild.channels, id=int(payment.channelid))
            
            member: discord.Member = utils.get_channel_member(channel)

            await channel.send(f"{member.mention}\n", embed=AccountDoneEmbed, view=views.PaymentConfirmation(self.bot.db, self.bot))
            await ctx.send(f"Payment for {currentPayment.user} is made, waiting for user's confirmation")
        
        elif (utils.in_ticket(ctx)):
            currentPayment: Payment = await self.bot.db.set_payment_done(ctx.channel.id)

            member: discord.Member = utils.get_channel_member(ctx.channel)

            await ctx.message.delete()
            await ctx.send(f"{member.mention}\n", embed=AccountDoneEmbed, view=views.PaymentConfirmation(self.bot.db, self.bot))
            await self.bot.admin_panel.send(f"{ctx.author.mention}\nPayment for {currentPayment.user} is made, waiting for user's confirmation")

    @commands.command()
    async def find(self, ctx: commands.Context, id: int):
        if (self.__inadminpanel(ctx)):
            account : OWAccount = await self.bot.db.get_account(id)

            if (account is None or account.channelid is None):
                await ctx.send("Account not yet associated with a user or channel")
                return

            channel = discord.utils.get(ctx.guild.channels, id=int(account.channelid))
            await ctx.send(f"Channel associated with account id {id}: {channel.mention}")

    @commands.command()
    async def upstock(self, ctx: commands.Context):
        if (self.__inadminpanel(ctx)):
            await self.bot.update_stock(True)
            await ctx.send("Updated stock status")

    @commands.command()
    async def createauth(self, ctx: commands.Context):
        if (self.__inadminpanel(ctx)):
            await ctx.send("Creating authenticator handlers")

            for row in await self.bot.db.get_secret_keys():
                if (row[0] not in self.bot.auth_handlers.keys() and row[1] != None):
                    b32code = base64.b32encode(bytes.fromhex(row[1])).decode()
                    self.bot.auth_handlers[row[0]] = totp.TOTP(b32code, 8)

            await ctx.send(f"Done creating {len(self.bot.auth_handlers)} authenticator handlers")



    @commands.command()
    @commands.has_any_role("Manager")
    async def code(self, ctx: commands.Context):
        await ctx.message.delete()

        user = utils.get_channel_member(ctx.channel)
        username = user.name + user.discriminator

        id = int(ctx.channel.name[(13 + len(username)):])
            
        if (id in self.bot.auth_handlers):
            await ctx.send(f"Code: {self.bot.auth_handlers[id].now()}")
            return
        
        await ctx.send("There is no any authenticators attached for this account")

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        if (isinstance(error, commands.errors.MissingAnyRole)):
            await ctx.message.delete()
            await ctx.send("You don't have the permission to use this command")

    #To check if the commnd called in the right place
    def __inadminpanel(self, ctx: commands.Context):
        return ctx.channel == self.bot.admin_panel

async def setup(bot: commands.Bot):
    await bot.add_cog(Administration(bot))