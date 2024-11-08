import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up Discord intents
intents = discord.Intents.default()
intents.members = True

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="!help for commands"))
    print("Bot is online and ready!")

async def start_bot():
    await bot.start(os.getenv('TOKEN_DS'))

async def setup(bot):
    # Load the Events cog
    await bot.add_cog(Events(bot))

    # Start the bot
    await start_bot()

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Run the setup and start the bot
if __name__ == "__main__":
    import asyncio
    asyncio.run(setup(bot))