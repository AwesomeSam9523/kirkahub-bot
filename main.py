import discord
from discord.ext import commands
import asyncio

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

@bot.event
async def on_member_join(member:discord.Member):
    pass

@bot.event
async def on_member_remove(member:discord.Member):
    pass

async def one_ready():
    await bot.wait_until_ready()
    print("Ready!")

asyncio.create_task(one_ready())
bot.run("OTAyMjUwNjQ2NzgxMTY5Njg1.YXbsZQ.n_2ihr6mfQI38s_dvpww265yL80")