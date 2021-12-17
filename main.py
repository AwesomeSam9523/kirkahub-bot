import datetime
from discord.ext.commands import Context
import discord
from discord.ext import commands, tasks
import asyncio, aiohttp
import requests
from typing import Union
saycmd = {}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

def onlystaff(ctx:Context):
    if ctx.guild.get_role(868890524843638804) not in ctx.author.roles:
        return False
    return True

@bot.event
async def on_member_join(member:discord.Member):
    count = member.guild.member_count
    if str(count)[:-1] == "1":
        anno = "st"
    elif str(count)[:-1] == "2":
        anno = "nd"
    elif str(count)[:-1] == "3":
        anno = "rd"
    else:
        anno = "th"
    embed = discord.Embed(title="Welcome to Kirka Hub!",
                          description=f"**You are our {count}{anno}** member!\n\n"
                                      f"Head over to <#868890525565079595> for any basic information you may need and "
                                      f"make sure to equip cool roles from <#868890525565079598> 😎",
                          color=3342080)
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_thumbnail(url=member.display_avatar.url or member.default_avatar.url)
    await bot.get_channel(868890526433280027).send(f"{member.mention}", embed=embed)

@bot.event
async def on_member_remove(member:discord.Member):
    count = member.guild.member_count
    embed = discord.Embed(title="Goodbye :(",
                          description=f"{member.mention} just left. We now have {count} members.",
                          color=16711680)
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_thumbnail(url=member.display_avatar.url or member.default_avatar.url)
    await bot.get_channel(868890526433280027).send(embed=embed)

@bot.command()
@commands.check_any(onlystaff, is_owner)
async def steal(ctx:Context, name:str, emoji:Union[discord.Emoji, str]=None):
    url = ""
    if isinstance(emoji, discord.Emoji):
        url = emoji.url
    elif isinstance(emoji, str):
        url = emoji
    elif emoji is None and len(ctx.message.attachments) != 0:
        url = ctx.message.attachments[0].url
    else:
        await ctx.send("Incorrect Syntax! Use `!steal <name> [url or emoji or file-attachment]`")

    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            r.raw.decode_content = True
            a = r.content
            name = name.replace(" ", "_")
            if len(name) < 2:
                return await ctx.reply("Name should be minimum 2 characters long")
            newemoji = await ctx.guild.create_custom_emoji(name=name, image=a)
            await ctx.reply(f"Added emoji successfully!\nEmoji: {newemoji}\nName: {newemoji.name}\nCode: `{'a' if newemoji.animated else ''}:{newemoji.name}:{newemoji.id}`")
        else:
            await ctx.reply("Invalid URL")
    except Exception as e:
        await ctx.send(f"An error occured: {e}")

@bot.command()
@commands.check_any(onlystaff, is_owner)
async def say(ctx, *, sentence):
    chl = sentence.split(" ")[0]
    chlmodified = False
    testchl = chl.replace("<#", "").replace(">", "")
    if len(testchl) == len("839080243485736970"):
        try:
            chl = int(testchl)
            saycmd[str(ctx.author.id)] = chl
            chlmodified = True
        except Exception as e:
            pass
    chnid = saycmd.get(str(ctx.author.id))
    if chnid is None:
        return await ctx.reply("No last used channel found! Use `!say <#channel> <sentence>` for first time")
    chn = bot.get_channel(chnid)
    try:
        if chlmodified:
            sentence = " ".join(sentence.split(" ")[1:])
        await chn.send(sentence)
    except:
        ctx.reply("An error occured. Make sure I have sufficient permission in the channel to talk")

@bot.command()
async def bgtos(ctx):
    await ctx.reply("Use `;bgtos` instead.")

tidesc = """**How to setup KirkaClient Twitch Integration:**\n
1. Make a new Twitch Account
2. Name it whatever you wish (it will be bot's name)
3. Go to https://twitchapps.com/tmi/ and authorize with new account
4. Copy the token to clipboard
5. Open KirkaClient
6. Enter Username as your bot's name
7. Enter OAuth token as token you copied
8. Enter Channel as your main twitch channel
9. Restart client
"""
    
@bot.command(aliases=['twitch'])
async def ti(ctx):
    embed = discord.Embed(title="Twitch Integration",
                         description=tidesc)
    embed.set_image(url="https://media.discordapp.net/attachments/868890525871247451/913617441106571304/unknown.png")
    await ctx.send(embed=embed)

@tasks.loop(seconds=30)
async def botStatus():
    kh = bot.get_guild(868890520468983819)
    booster = kh.get_role(868890520527732799)
    staff = kh.get_role(868890524843638804)
    for i in kh.members:
        if i in kh.premium_subscribers and booster not in i.roles:
            await i.add_roles(booster)
            print(f'Added booster role to {i}')
        if i not in kh.premium_subscribers and booster in i.roles and staff not in i.roles:
            await i.remove_roles(booster)
            print(f'Removed booster role of {i}')
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://kirkaclient.herokuapp.com/api/users") as a:
            a = await a.json()
            count = a["count"]
            if count == 1:
                sense = 'user'
            else:
                sense = 'users'
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"KirkaClient {f'with {count} {sense}' if count else ''}"),
                                      status=discord.Status.dnd)
            
@bot.command(aliases=['eval'], hidden=True)
@commands.is_owner()
async def evaluate(ctx, *, expression):
    try:
        await ctx.reply(eval(expression))
    except Exception as e:
        await ctx.reply(f'```\n{e}```')

@bot.command(aliases=['exec'], hidden=True)
@commands.is_owner()
async def execute(ctx, *, expression):
    try:
        exec(expression)
    except Exception as e:
        await ctx.reply(f'Command:```py\n{expression}```\nOutput:```\n{e}```')
    
    
@bot.event
async def on_ready():
    print("Ready!")
    botStatus.start()

bot.run("OTAyMjUwNjQ2NzgxMTY5Njg1.YXbsZQ.n_2ihr6mfQI38s_dvpww265yL80")
