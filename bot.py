import discord
import typing
import os

import asyncio

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
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
GUILD_ID = os.getenv("SERVER_ID")

discord.utils.setup_logging()

class AccountManager(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

        self.db = DBManager(DB_USER, DB_PASS, DB_HOST, DB_NAME)

        self.request_channel : discord.TextChannel = None
        self.admin_panel : discord.TextChannel = None
        self.stock_channel: discord.TextChannel = None

        self.stock_update : discord.Message = None

        self.accounts = {
            "total": 0,
            "0r": 0,
            "1r": 0,
            "2r": 0,
            "3r": 0
        }

    async def on_ready(self):
        await super().wait_until_ready()
        
        await self.db.create_tables()

        super().add_view(views.TicketStarterView(self.db, self))
        super().add_view(views.TicketDone(self.db))
        super().add_view(views.PaymentConfirmation(self.db))

        self.main_guild = super().get_guild(int(GUILD_ID))
        if (self.main_guild is not None): 
            self.admin_panel = discord.utils.get(self.main_guild.text_channels, name="admin-panel")
            self.request_channel = discord.utils.get(self.main_guild.text_channels, name="account-request")
            self.stock_channel = discord.utils.get(self.main_guild.text_channels, name="stock-status")

            self.stock_update = await self.stock_channel.fetch_message(self.stock_channel.last_message_id)

            #Update stock on start
            self.accounts["total"], self.accounts["0r"], self.accounts["1r"], self.accounts["2r"], self.accounts["3r"] = await self.db.get_supply_size()
            await self.update_stock()
            
        print("Bot is connected and online")
        


        #TODO: Fix if needed
        ''''
        if self.request_channel is not None:
            last_msg = await self.request_channel.fetch_message(self.request_channel.last_message_id)

        if last_msg.content == "The bot is currently closed you can request an account when it is back online":
            await last_msg.delete()'''


    async def on_guild_join(self, guild: discord.Guild):    
        adminPanelPermissions = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        #Stock channel will also share the same permission
        ticketChannelPermission = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        if self.admin_panel is not None:
            print("Server already has channels, not creating new ones")
        else:
            ticketEmbed = discord.Embed(title="Account request", description="If you want an account to start playing please click the button below to start a ticket. If you have been already given an account, a new one cannot be given")

            adminCat = await guild.create_category(name="admin", overwrites=adminPanelPermissions)
            ticketCat = await guild.create_category(name="tickets")
            stockCat = await guild.create_category(name="stock")

            self.request_channel = await guild.create_text_channel(name="account-request", category=ticketCat, overwrites=ticketChannelPermission)
            self.stock_channel = await guild.create_text_channel(name="stock-status", category=stockCat, overwrites=ticketChannelPermission)

            self.stock_update = await self.stock_channel.send(
                content=f"""**Current Stock**
Available Accounts: {self.accounts["total"]}

**Accounts needed:**
50 Wins: {self.accounts["0r"]}

One role: {self.accounts["1r"]}

Two role: {self.accounts["2r"]}

Three role: {self.accounts["3r"]}
_ _
""")          
            await self.request_channel.send(embed=ticketEmbed, view=views.TicketStarterView(self.db, self))
            #Create the administrator panel
            self.admin_panel = await guild.create_text_channel(name="admin-panel", overwrites=adminPanelPermissions, category=adminCat) 

    async def update_stock(self, pull: bool = False):

        if pull:
            self.accounts["total"], self.accounts["0r"], self.accounts["1r"], self.accounts["2r"], self.accounts["3r"] = await self.db.get_supply_size()

        await self.stock_update.edit(content=f"""**Current Stock**
Available Accounts: {self.accounts["total"]}

**Accounts needed:**
50 Wins: {self.accounts["0r"]}

One role: {self.accounts["1r"]}

Two role: {self.accounts["2r"]}

Three role: {self.accounts["3r"]}
_ _
""")

'''

@bot.command()
async def close(ctx: commands.Context):
    if (ctx.channel.name == "admin-panel"):
        await ctx.send("Closing bot")

        channel = discord.utils.get(ctx.guild.channels, name="account-request")
        await channel.send("The bot is currently closed you can request an account when it is back online")
        
        await bot.close()

'''
AccountBot = AccountManager()

async def main():
    async with AccountBot:
        await AccountBot.load_extension("cogs.administration")
        await AccountBot.load_extension("cogs.dev")
        await AccountBot.start(TOKEN)

if (__name__ == "__main__"):
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Closing")

