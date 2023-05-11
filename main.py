import datetime
from discord.ext.commands import Context
import discord
from discord.ext import commands, tasks
import asyncio, aiohttp
import requests
from typing import Union
from pymongo import MongoClient
import json
import time
saycmd = {}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")
bot.updating, bot.notif = False, False

client = MongoClient("mongodb+srv://bot:2fvx3GuVU76z24X@cluster0.kthop.mongodb.net/kirkaclient?retryWrites=true&w=majority")
clientdb = client.kirkaclient
db = clientdb.badges

def addBadge(badgetype, value):
    id = {"name": badgetype}
    old = db.find_one(id)["value"]
    if value in old:
        return {"code": 400, "msg": "Badge already exists!"}
    db.find_one_and_update(id, {"$push": {"value": value}})
    return {"code": 200, "msg": "Added successfully!"}

def removeBadge(badgetype, value):
    id = {"name": badgetype}
    old = db.find_one(id)["value"]
    if value not in old:
        return {"code": 400, "msg": "Badge doesn't exists!"}
    db.find_one_and_update(id, {"$pull": {"value": value}})
    return {"code": 200, "msg": "Removed successfully!"}

def onlystaff(ctx:Context):
    if ctx.author.id == 771601176155783198:
        return True
    if ctx.guild.get_role(868890524843638804) not in ctx.author.roles:
        return False
    return True

def onlyadmin(ctx:Context):
    if ctx.author.id == 771601176155783198:
        return True
    if ctx.guild.get_role(868890524755582995) not in ctx.author.roles:
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
    embed = discord.Embed(
        title="Welcome to Kirka Hub!",
        description=f"**You are our {count}{anno}** member!\n\n"
                    f"Head over to <#868890525565079595> for any basic information you may need and "
                    f"make sure to equip cool roles from <#868890525565079598> 😎",
        color=3342080
    )
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_thumbnail(url=member.display_avatar.url or member.default_avatar.url)
    await bot.get_channel(868890526433280027).send(f"{member.mention}", embed=embed)

@bot.event
async def on_member_remove(member:discord.Member):
    count = member.guild.member_count
    embed = discord.Embed(
        title="Goodbye :(",
        description=f"{member} just left. We now have {count} members.",
        color=16711680
    )
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_thumbnail(url=member.display_avatar.url or member.default_avatar.url)
    await bot.get_channel(868890526433280027).send(embed=embed)

@bot.command()
@commands.check(onlystaff)
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

async def getResponse(ctx):
    def check(msg):
        return msg.channel == ctx.channel and msg.author == ctx.author

    msg = await bot.wait_for('message', check=check)
    return msg

#@bot.command(usage="`!badge add/del <type> <user>`")
#@commands.check(onlyadmin)
async def badge(ctx: Context, action: str = None, badgetype: str = None, value: str = None):
    if not action or not badgetype or not value:
        return await ctx.reply(ctx.command.usage)
    
    action, badgetype = action.lower(), badgetype.lower()
    if action not in ["add", "del"]:
        return await ctx.reply(ctx.command.usage)
    
    allowedTypes = ["patreon", "con", "dev", "nitro", "staff", "gfx", "vip", "kdev", "custom"]
    if badgetype not in allowedTypes:
        return await ctx.reply(f"BadgeType can only be: `{', '.join(allowedTypes)}`")
    
    if badgetype != "custom":
        if action == "add":
            res = addBadge(badgetype, value)
        else:
            res = removeBadge(badgetype, value)
        
        return await ctx.reply(f"`[{res['code']}]` {res['msg']}")
    
    await ctx.send('Upload the image from your PC as an attachment. The image should be 512x512.\n'+
                '__Note:__ It is your duty to ensure the same. Please ask the patreon to fix that if its less than desired size.')
    while True:
        msg: discord.Message = await getResponse(ctx)
        if len(msg.attachments) > 0:
            break
    attch = msg.attachments[0].url
    if attch[-3:].lower() not in ['png', 'jpg', 'jpeg']:
        return await ctx.send('Image not a `PNG/JPG` file. Aborted!')
    await ctx.send('Enter the motto. Make sure its not NSFW or inappropriate.')
    msg = await getResponse(ctx)
    motto = msg.content

    data = {
        'url': attch,
        'role': motto,
        'type': value.lower(),
        'name': value
    }
    
    id = {"name": "custom"}
    old = db.find_one(id)["value"]
    new = []

    for badge in old:
        if badge["name"] == value:
            new.append(data)
        else:
            new.append(badge)
    
    db.find_one_and_update(id, {"$set": {"value": new}})
    await ctx.send('Updated Successfully!')
    embed = discord.Embed(description=f"Please update the badge of `{value}` at [Discord Dev Portal](<https://discord.com/developers/applications/871730144836976650/rich-presence/assets>) to the [new Image]({attch}). Add \\✔️ reaction on this message once its done!")
    await bot.get_channel(868890525871247452).send(f'<@&868890524843638806>s', embed=embed)

#@bot.command()
#@commands.check(onlyadmin)
async def badges(ctx: Context):
    a = ["patreon", "con", "dev", "nitro", "staff", "gfx", "vip", "kdev"]
    embed = discord.Embed(title="List of Badges")
    for i in a:
        data = db.find_one({"name": i})["value"]
        data = "\n".join(data) if len(data) != 0 else "-"
        embed.add_field(name=f"`{i}`", value=f"```\n{data}```")
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def update(ctx: Context):
    bot.updating = True
    await ctx.send('Switched to update mode for 300 secs.')

@bot.command()
@commands.is_owner()
async def done(ctx: Context):
    bot.updating = False
    await ctx.send('Switched back to prod mode.')

@bot.command()
@commands.check(onlystaff)
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

tidesc = """
**How to setup KirkaClient Twitch Integration:**\n
1. Go to https://twitchapps.com/tmi/ and authorize with twitch account
2. Copy the token to clipboard
3. Open KirkaClient
4. Enter Username as your bot's name
5. Enter OAuth token as token you copied
6. Enter Channel as your main twitch channel
7. Restart client
"""

@bot.command(aliases=['twitch'])
async def ti(ctx):
    embed = discord.Embed(
        title="Twitch Integration",
        description=tidesc
    )
    embed.set_image(url="https://media.discordapp.net/attachments/868890525871247451/913617441106571304/unknown.png")
    await ctx.send(embed=embed)

@tasks.loop(seconds=30)
async def botStatus():
    kh = bot.get_guild(868890520468983819)
    booster = kh.get_role(868890520527732799)
    staff = kh.get_role(868890524843638804)
    respected = kh.get_role(868890520527732797)
    for i in kh.members:
        if i in kh.premium_subscribers and booster not in i.roles:
            await i.add_roles(booster)
            print(f'Added booster role to {i}')
        if i not in kh.premium_subscribers and booster in i.roles and (staff not in i.roles or respected not in i.roles):
            await i.remove_roles(booster)
            print(f'Removed booster role of {i}')
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://client.kirka.io/api/users") as a:
            if a.status != 200:
                return
            a = await a.json()
            count = a["count"]
            if count == 1:
                sense = 'user'
            else:
                sense = 'users'
            await bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.playing,
                name=f"KirkaClient {f'with {count} {sense}' if count else ''}"),
                status=discord.Status.idle
            )
            
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

ONLINE_STATUS = "<:status_online:1106062321647878144>"
INVISIBLE_STATUS = "<:status_invisible:1106062593409433680>"
IDLE_STATUS = "<:status_idle:1106062645561405493>"
DND_STATUS = "<:status_dnd:1106062696044056630>"

last_seen_map = {
    771601176155783198: 0,
    1091619634404401223: 0
}
bot.last_seen_msg: discord.Message = None
last_mobile_map = {
    771601176155783198: False,
    1091619634404401223: False
}
last_status_map = {
    771601176155783198: discord.Status.offline,
    1091619634404401223: discord.Status.offline
}

def get_user_status(member_id, member_status, web):
    status_text = ""
    last_seen = None
    if web:
        status_text = "🖥️ "
    else:
        status_text = "📱 "

    if member_status == discord.Status.online:
        status_text += ONLINE_STATUS
    elif member_status == discord.Status.offline:
        status_text += INVISIBLE_STATUS
        last_seen = int(time.time())
    elif member_status == discord.Status.idle:
        status_text += IDLE_STATUS
    elif member_status == discord.Status.dnd:
        status_text += DND_STATUS
    elif member_status == discord.Status.invisible:
        status_text += INVISIBLE_STATUS
        last_seen = int(time.time())

    return status_text, last_seen

@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if before.guild.id != 1091742337606107138:
        return
    if before.id not in [771601176155783198, 1091619634404401223]:
        return

    earlier_web = not before.is_on_mobile()
    later_web = not after.is_on_mobile()
    if before.is_on_mobile():
        before_status = before.mobile_status or before.status or before.web_status or before.desktop_status
    else:
        before_status = before.status or before.web_status or before.desktop_status
    if after.is_on_mobile():
        after_status = after.mobile_status or after.status or after.web_status or after.desktop_status
    else:
        after_status = after.status or after.web_status or after.desktop_status
    
    last_mobile_map[before.id] = after.is_on_mobile()
    last_status_map[before.id] = after_status

    before_text, _ = get_user_status(before.id, before_status, earlier_web)
    after_text, last_seen = get_user_status(after.id, after_status, later_web)

    if before_text != after_text:
        await bot.get_channel(1106059865698345040).send(
            f"{before}: {before_text} `->` {after_text}"
    )
        print(f"{before}: {before_text} `->` {after_text}")

    if last_seen:
        last_seen_map[before.id] = last_seen

    sam_status = bot.get_guild(1091742337606107138).get_member(771601176155783198).status
    if sam_status == discord.Status.offline:
        sam_last_seen = last_seen_map[771601176155783198]
        last_seen_text = f"AwesomeSam: <t:{sam_last_seen}:d> <t:{sam_last_seen}:t> (<t:{sam_last_seen}:R>)"
    else:
        sam_text, _ = get_user_status(771601176155783198, sam_status, False)
        last_seen_text = f"AwesomeSam: {sam_text}"

    patatar_status = bot.get_guild(1091742337606107138).get_member(1091619634404401223).status
    if patatar_status == discord.Status.offline:
        patatar_last_seen = last_seen_map[1091619634404401223]
        last_seen_text += f"\nPatatar: <t:{patatar_last_seen}:d> <t:{patatar_last_seen}:t> (<t:{patatar_last_seen}:R>)"
    else:
        patatar_text, _ = get_user_status(1091619634404401223, patatar_status, False)
        last_seen_text += f"\nPatatar: {patatar_text}"

    if bot.last_seen_msg:
        await bot.last_seen_msg.edit(content=last_seen_text)
    else:
        bot.last_seen_msg = await bot.get_channel(1106067025173942342).send(last_seen_text)

bot.run("OTAyMjUwNjQ2NzgxMTY5Njg1.YXbsZQ.wsUVrFWcGyuzG0rz728U1A7NO1U")
