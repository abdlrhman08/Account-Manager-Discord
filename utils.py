import discord
import messages

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

Authenticator WinAuth Secret Key: {account.hex_secret_key}
Restore Code: {account.restore_code}
Serial: {account.serial}

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
**50 Wins:** {accounts_dict["0Total"]}
    Sojourn: {accounts_dict["1"]}
    Kiriko: {accounts_dict["2"]}
    Life Weaver: {accounts_dict["3"]}
    Junker Queen: {accounts_dict["4"]}
    Ramattra: {accounts_dict["5"]}
    Illari: {accounts_dict["6"]}

**One role:** {accounts_dict["1Total"]}
    Tank: {accounts_dict["11"]}
    Dps: {accounts_dict["12"]}
    Support: {accounts_dict["13"]}
    Rank Up: {accounts_dict["14"]}

**Two role:** {accounts_dict["2Total"]}
    Dps and Support: {accounts_dict["21"]}
    Tank and Dps: {accounts_dict["22"]}

***Three role:*** {accounts_dict["30"]}
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
    
    @classmethod
    def populate_options(self, stock: dict, select: discord.ui.Select, main_type: int):
    
        if (main_type == 0):
            for i in range(6):
                dict_key = str(i + 1)
                if (stock[dict_key] > 0):
                    select.add_option(label=messages.TYPES[i], value=str(i))


        elif (main_type == 1):
            for i in range(11, 15):
                dict_key = str(i)
                if (stock[dict_key] > 0):
                    select.add_option(label=messages.TYPES[i - 5], value=str(i - 10))

        elif (main_type == 2):
            for i in range(21, 23):
                dict_key = str(i)
                if (stock[dict_key] > 0):
                    select.add_option(label=messages.TYPES[i - 11], value=str(i - 20))


