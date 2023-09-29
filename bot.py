import discord
import messages

from discord.ext import commands

from views import views
from utils import utils

from dbmanager.dbmanager import DBManager

class AccountManager(commands.Bot):

    def __init__(self, db_user, db_pass, db_host, db_name, guild_id):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

        self.db = DBManager(db_user, db_pass, db_host, db_name)

        self.guild_id = guild_id

        self.request_channel : discord.TextChannel = None
        self.admin_panel : discord.TextChannel = None
        self.stock_channel: discord.TextChannel = None

        self.stock_update : discord.Message = None

        self.trusted_role : discord.Role = None
        self.manager_role: discord.Role = None

        self.finished_cat: discord.CategoryChannel = None
        self.paid_cat: discord.CategoryChannel = None

        self.auth_handlers = {}
        self.accounts = {
            "total": 0,
            "0Total": 0,
            "1Total": 0,
            "2Total": 0,
            "1": 0,     #Sojourn     
            "2": 0,     #kiriko
            "3": 0,     #LW
            "4": 0,     #JQ
            "5": 0,     #Ramattra
            "6": 0,     #Illari
            "11": 0,    #Tank
            "12": 0,    #DPS
            "13": 0,    #Support
            "14": 0,    #Rank up
            "21": 0,    #Dps + Support
            "22": 0,    #Tank + Dps
            "30": 0
        }

    async def on_ready(self):
        await super().wait_until_ready()
        
        await self.db.create_tables()

        super().add_view(views.TicketStarterView(self.db, self))
        super().add_view(views.TicketDone(self.db, self))
        super().add_view(views.PaymentConfirmation(self.db, self))

        self.main_guild = super().get_guild(int(self.guild_id))
        if (self.main_guild is not None): 
            self.admin_panel = discord.utils.get(self.main_guild.text_channels, name="admin-panel")
            self.request_channel = discord.utils.get(self.main_guild.text_channels, name="account-request")
            self.stock_channel = discord.utils.get(self.main_guild.text_channels, name="stock-status")

            self.finished_cat = discord.utils.get(self.main_guild.categories, name="marked-as-finished")
            self.paid_cat = discord.utils.get(self.main_guild.categories, name="paid-and-closed")

            self.stock_update = await self.stock_channel.fetch_message(self.stock_channel.last_message_id)

            self.trusted_role = discord.utils.get(self.main_guild.roles, name="Trustees")
            self.manager_role = discord.utils.get(self.main_guild.roles, name="Manager")

            #Update stock on start
            #self.accounts["total"], self.accounts["0"], self.accounts["1"], self.accounts["2"], self.accounts["3"] = await self.db.get_supply_size()
            #await self.update_stock()
            
            await self.update_stock(True)
            print(self.accounts)

        print("Bot is connected and online")
        


        #TODO: Fix if needed
        ''''
        if self.request_channel is not None:
            last_msg = await self.request_channel.fetch_message(self.request_channel.last_message_id)

        if last_msg.content == "The bot is currently closed you can request an account when it is back online":
            await last_msg.delete()'''


    async def on_guild_join(self, guild: discord.Guild):
        self.manager_role = discord.utils.get(guild.roles, name="Manager")


        adminPanelPermissions = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),

            self.manager_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        #Stock channel will also share the same permission
        ticketChannelPermission = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        self.trusted_role = discord.utils.get(guild.roles, name="Trustees")

        if self.admin_panel is not None:
            print("Server already has channels, not creating new ones")
        else:
            ticketEmbed = discord.Embed(title="Account request", description=messages.MESSAGES["REQUEST_CHANNEL"])

            adminCat = await guild.create_category(name="admin", overwrites=adminPanelPermissions)
            stockCat = await guild.create_category(name="stock")
            ticketCat = await guild.create_category(name="tickets")

            self.finished_cat = await guild.create_category(name="marked-as-finished", overwrites=adminPanelPermissions)
            self.paid_cat = await guild.create_category(name="paid-and-closed", overwrites=adminPanelPermissions)

            self.request_channel = await guild.create_text_channel(name="account-request", category=ticketCat, overwrites=ticketChannelPermission)
            self.stock_channel = await guild.create_text_channel(name="stock-status", category=stockCat, overwrites=ticketChannelPermission)

            self.stock_update = await self.stock_channel.send(content=utils.stock_msg_content(self.accounts))

            await self.update_stock(True)          
            await self.request_channel.send(embed=ticketEmbed, view=views.TicketStarterView(self.db, self))
            #Create the administrator panel
            self.admin_panel = await guild.create_text_channel(name="admin-panel", overwrites=adminPanelPermissions, category=adminCat) 

    async def on_guild_remove(self, guild: discord.Guild):
        self.admin_panel = None
        self.request_channel = None
        self.stock_channel = None
        self.stock_update = None
    
    async def update_stock(self, pull: bool = False):

        if pull:
            await self.db.get_supply_size(self.accounts)

        await self.stock_update.edit(content=utils.stock_msg_content(self.accounts))

'''

@bot.command()
async def close(ctx: commands.Context):
    if (ctx.channel.name == "admin-panel"):
        await ctx.send("Closing bot")

        channel = discord.utils.get(ctx.guild.channels, name="account-request")
        await channel.send("The bot is currently closed you can request an account when it is back online")
        
        await bot.close()

'''


