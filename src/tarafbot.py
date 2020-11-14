import os
from discord.ext import commands
from tarcog import TarCog
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

bot.add_cog(TarCog(bot))

bot.run(TOKEN)
