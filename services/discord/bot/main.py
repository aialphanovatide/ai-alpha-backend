import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="!help for commands"))
    print("Bot is online and ready!")

async def start_bot():
    await bot.start(os.getenv('TOKEN_DS'))

if __name__ == "__main__":
    import asyncio
    from events import setup

    asyncio.run(setup(bot))
    asyncio.run(start_bot())
