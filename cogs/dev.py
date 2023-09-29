import typing
import discord

from views import views

from discord.ext import commands

from utils import utils

class Development(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload", hidden=True)
    async def _reload(self, ctx: commands.Context, extension: typing.Optional[str]):
        if (utils.is_admin(ctx)):

            if (extension is None):
                #TODO: reload all
                pass

            await self.bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"Reloaded extension: {extension}")

    @commands.command()
    async def generate(self, ctx: commands.Context, id: int):
        if (utils.is_admin(ctx)):
            channel: discord.TextChannel = discord.utils.get(self.bot.main_guild.text_channels, id=id)

            await channel.send(embed=self.bot.ticketEmbed, view=views.TicketStarterView(self.bot.db, self.bot))
async def setup(bot: commands.Bot):
    await bot.add_cog(Development(bot))