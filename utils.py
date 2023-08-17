import discord

from dbmanager.models import OWAccount

from discord.ext import commands

class utils():

    @classmethod
    def export(self, account: OWAccount) -> str:
        type: str
        name = account.name.split()

        if (account.type == 0):
            type = "50 Wins"
        else:
            type = str(account.type) + " Role"

        return f"""Info for {account.user} given account
Created: {account.creation_date}
Finished: {account.finished_date}

Recovery mail: {account.email}
Email Password: {account.email_password}

Battle Tag: {account.battle_tag}
Battle.net Password: {account.password}

Account Type: {type}

Country: Latvia
Phone: {account.phonenum}
Birthdate: {account.birthdate}

First Name: {name[0]}
Last Name: {name[1]}

SafeUM User: {account.safe_um_user}
SafeUM Pass: {account.safe_um_pass}

Description: {account.description}"""
    
    @classmethod
    def get_channel_member(self, channel: discord.TextChannel):
        member_role : discord.Role = discord.utils.get(channel.guild.roles, name="Trustees")

        for member in channel.members:
            if (member_role in member.roles):
                return member

    @classmethod
    def stock_msg_content(self, accounts_dict: dict):
        return f"""**Current Stock**
Available Accounts: {accounts_dict["total"]}

**Accounts needed:**
50 Wins: {accounts_dict["0"]}

One role: {accounts_dict["1"]}

Two role: {accounts_dict["2"]}

Three role: {accounts_dict["3"]}
_ _
"""        
    
    @classmethod
    def is_admin(self, bot, ctx: commands.Context):
        return ctx.author == ctx.guild.owner or  bot.manager_role in ctx.author.roles
    
    @classmethod
    def in_ticket(self, ctx: commands.Context):
        return "account-for" in ctx.channel.name
    
    @classmethod
    def check_ticket(self, bot, interaction: discord.Interaction):
        return bot.manager_role not in interaction.user.roles
