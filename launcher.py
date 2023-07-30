import asyncio
import discord
import os

from bot import AccountManager

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
GUILD_ID = os.getenv("SERVER_ID")

discord.utils.setup_logging()

AccountBot = AccountManager(
    DB_USER,
    DB_PASS,
    DB_HOST,
    DB_NAME,
    GUILD_ID
)

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