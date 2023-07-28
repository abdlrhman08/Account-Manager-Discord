import discord
import typing

from discord.ext import commands

from dbmanager.models import OWAccount, Payment 
from utils import utils
from views import views

class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def done(self, ctx: commands.Context):
        if (self.__inadminpanel(ctx)):   
            FinishedAccountEmbed = discord.Embed(title="Finished Accounts")

            account: OWAccount
            finishedAccounts = await self.bot.db.get_finished_accounts()

            if len(finishedAccounts) != 0:
                for account in finishedAccounts:
                    FinishedAccountEmbed.add_field(name="", value=f"ID: {account.id}, E-mail: {account.email}", inline=False)
            else:
                FinishedAccountEmbed.add_field(name="", value="There is no any finished accounts currently", inline=False)

            FinishedAccountEmbed.add_field(name="More help..", value="To export full info, use the command !export [email]", inline=False)

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

        elif ("account-for-" in ctx.channel.name and ctx.author == ctx.guild.owner):
            account = await self.bot.db.get_account_by_channel(str(ctx.channel.id))

            #TODO: add the export feature
            #DONE
            info = utils.export(account)
            
            await ctx.message.delete()
            await self.bot.admin_panel.send(f"{ctx.guild.owner.mention}\n" + info)

    @commands.command()
    async def schedule(self, ctx: commands.Context, id: typing.Optional[int], amount: typing.Optional[int], date: typing.Optional[str]):
        if (utils.is_admin(self.bot, ctx)):

            if ("account-for-" in ctx.channel.name):
                payment = await self.bot.db.get_payment_by_id(id)

                await ctx.message.delete()
                await self.bot.db.set_payment_info(id, date, amount)

                member = utils.get_channel_member(ctx.channel)

                await ctx.send(f"{member.mention}\nAccount has been checked and payment has been scheduled for {date}")
            
            elif (self.__inadminpanel(ctx)):
                payments = await self.bot.db.get_payments()

                scheduledPaymentsEmbed = discord.Embed(title="Scheduled payments")

                if len(payments) == 0:
                    scheduledPaymentsEmbed.add_field(name="", value="No current payments registered")

                payment: Payment
                for payment in payments:
                    date = payment.paymentDate

                    if date is None:
                        date = "Unscheduled"

                    scheduledPaymentsEmbed.add_field(name="", value=f"Process ID: {payment.id}, User: {payment.user}, Number: {payment.paymentNum}, Amount: {payment.amount}, Date: {date}, Paid: {payment.payed}, Confirmed: {payment.confirmed}", inline=False)

                await ctx.send(embed=scheduledPaymentsEmbed)

    @commands.command()
    async def accounts(self, ctx: commands.Context):
        accounts = await self.bot.db.get_accounts()

        AccountsEmbed = discord.Embed(title="Current accounts on database")

        if len(accounts) == 0:
            AccountsEmbed.add_field(name="", value="No current payments registered")

            account: OWAccount
            for account in accounts:
                AccountsEmbed.add_field(name="", value=f"Account ID: {account.id}, User: {account.user}, Finished: {account.finished}", inline=False)

        await ctx.send(embed=AccountsEmbed)
                

    @commands.command()
    async def paid(self, ctx: commands.Context, id: int):
        if (self.__inadminpanel(ctx)):
            currentPayment : Payment = await self.bot.db.set_payment_done(id)

            AccountDoneEmbed = discord.Embed(title="Payment placed", description=f"Your scheduled paymen has been placed, please confirm your payment after receiving using the button below. You will be asked to write the amount received")
            
            payment = await self.bot.db.get_payment_by_id(id)

            channel = discord.utils.get(ctx.guild.channels, id=int(payment.channelid))
            
            member: discord.Member = utils.get_channel_member(channel)

            await channel.send(f"{member.mention}\n", embed=AccountDoneEmbed, view=views.PaymentConfirmation(self.bot.db))
            await ctx.send(f"Payment for {currentPayment.user} is made, waiting for user's confirmation")

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

    #To check if the commnd called in the right place
    def __inadminpanel(self, ctx: commands.Context):
        return ctx.channel == self.bot.admin_panel


async def setup(bot: commands.Bot):
    await bot.add_cog(Administration(bot))