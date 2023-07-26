import discord

from dbmanager.models import OWAccount

from discord.ext import commands

class utils():

    @classmethod
    def export(self, account: OWAccount) -> str:
        type: str

        if (account.type == 0):
            type = "50 Wins"
        elif (account.type == 1):
            type = "1 Role"
        elif (account.type == 2):
            type = "2 Role"
        elif (account.type == 3):
            type = "3 Role"


        return f"""Info for {account.user} given account
Recovery mail: {account.email}
Battle Tag: {account.battle_tag}
Password: {account.password}
Account Type: {type}
Phone: {account.phonenum}
SafeUM User: {account.safe_um_user}
SafeUM Pass: {account.safe_um_pass}
Description: {account.description}
Security Question: {account.security_q}
Answer: {account.q_ans}"""
    
    @classmethod
    def get_channel_member(channel: discord.TextChannel):
        for member in channel.members:
            if (member != channel.guild.me and member != channel.guild.owner):
                return member
            
    @classmethod
    def is_admin(self, ctx: commands.Context):
        return ctx.author == ctx.guild.owner 