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
DB_NAME = os.getenv("DB_NAME")
GUILD_ID = os.getenv("SERVER_ID")

discord.utils.setup_logging()

class AccountManager(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

        self.db = DBManager(DB_USER, DB_PASS, DB_NAME)

        self.request_channel : discord.TextChannel = None
        self.admin_panel : discord.TextChannel = None

        self.stock_update : discord.Message = None

        self.accounts_count = 0
        self.fresh_count = 0
        self.one_role_count = 0
        self.two_role_count = 0
        self.three_role_count = 0

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
            self.stock_update = [message async for message in self.request_channel.history(limit=1)][0]

            #Update stock on start
            self.accounts_count, self.fresh_count, self.one_role_count, self.two_role_count, self.three_role_count = await self.db.get_supply_size()
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

            self.request_channel = await guild.create_text_channel(name="account-request", category=ticketCat, overwrites=ticketChannelPermission)
            

            self.stock_update = await self.request_channel.send(
                content=f"""**Current Stock**
Available Accounts: {self.accounts_count}

**Accounts needed:**
50 Wins: {self.fresh_count}

One role: {self.one_role_count}

Two role: {self.two_role_count}

Three role: {self.three_role_count}
_ _
""")          
            await asyncio.sleep(10)
            await self.request_channel.send(embed=ticketEmbed, view=views.TicketStarterView(self.db, self))
            #Create the administrator panel
            self.admin_panel = await guild.create_text_channel(name="admin-panel", overwrites=adminPanelPermissions, category=adminCat) 

    async def update_stock(self, pull: bool = False):

        if pull:
            self.accounts_count, self.fresh_count, self.one_role_count, self.two_role_count, self.three_role_count = await self.db.get_supply_size()

        await self.stock_update.edit(content=f"""**Current Stock**
Available Accounts: {self.accounts_count}

**Accounts needed:**
50 Wins: {self.fresh_count}

One role: {self.one_role_count}

Two role: {self.two_role_count}

Three role: {self.three_role_count}
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

