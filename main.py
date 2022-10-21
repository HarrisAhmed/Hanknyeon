import disnake as discord
from disnake.ext import commands, tasks
from PIL import Image
from io import BytesIO
import asqlite
from views import Cards, Menu, DeleteView
from db import Hanknyeon
import os
from keep_alive import keep_alive
import random
from datetime import date
from tictactoe import TicTacToeView

intents = discord.Intents.all()
bot = Hanknyeon()


@bot.event
async def on_ready():
    print("I'm Alive")
    bot.conn = await asqlite.connect("main.db")
    await bot.get_cards_data()
    print(len(bot.data.keys()))
    check_limit.start()


@tasks.loop(seconds=2)
async def check_limit():
    limited_cards = await bot.limited_cards()
    
    for r in limited_cards:
        card = r[0]
        dated = r[1]
        if str(date.today()) >= dated:
            bot.data[card]["name"] = bot.data[card]["name"].split(" (")[0]
            await bot.delete_card(card, limit=True)
            print("done dana done")


def create(q, w, e):
    i1 = Image.open(f"pics/{q}").convert("RGBA")
    i2 = Image.open(f"pics/{w}").convert("RGBA")
    i3 = Image.open(f"pics/{e}").convert("RGBA")
    img = Image.new("RGBA", (2460, 1100), (0, 0, 0, 0))
    img.paste(i1, (0, 0), i1)
    img.paste(i2, (820, 0), i2)
    img.paste(i3, (1640, 0), i3)
    buff = BytesIO()
    img.save(buff, "png")
    buff.seek(0)
    return buff


def get_single(card):
    img = Image.open(f"pics/{card}").resize((820, 1100))
    buff = BytesIO()
    img.save(buff, "png")
    buff.seek(0)
    return buff

print(commands.BucketType.user)
@bot.slash_command(description="Drops card")
@commands.cooldown(1, 600, commands.BucketType.user)
async def drop(inter):
    data = bot.data
    await inter.response.defer()
    piclis = os.listdir("./pics")
    for key, value in bot.data.items():
        if bot.data[key]["name"].endswith("(Not Accessible)"):
            piclis.remove(key + ".png")
    r1 = [id for id in piclis if data[id[:-4]]["rarity"]==1]
    r2 = [id for id in piclis if data[id[:-4]]["rarity"]==2]
    r3 = [id for id in piclis if data[id[:-4]]["rarity"]==3]
    r4 = [id for id in piclis if data[id[:-4]]["rarity"]==4]
    r5 = [id for id in piclis if data[id[:-4]]["rarity"]==5]
    while True:
        q, w, e = random.sample(r1*60+r2*30+r3*15+r4*10+r5*5, 3)
        if q != w and w != e and e != q:
            break
    buff = await bot.loop.run_in_executor(None, create, q, w, e)
    q, w, e = q[:-4], w[:-4], e[:-4]
    emb = discord.Embed(
        description=f"{inter.author.mention} is dropping a set of 3 cards!",
        color=0x2F3136)
    emb.set_image(file=discord.File(buff, filename="image.png"))
    rarities = []
    names = []
    for i in (q, w, e):
        rarities.append(data[i]["rarity"])
        names.append(f"{data[i]['group']} {data[i]['name']}")
    view = Cards(rarities, names, (q, w, e))
    view.inter = inter
    view.bot = bot
    await inter.edit_original_message(
        embed=emb,
        view=view,
    )


@drop.error
async def on_drop_error(inter, error):
    if isinstance(error, commands.CommandOnCooldown):
        time = error.cooldown.get_retry_after()
        embed = discord.Embed(title="This command is on cooldown", description=f"Try using this command after {bot.sort_time(time)}.", color=discord.Color.red())
        await inter.send(embed=embed)


@bot.slash_command(description="Shows Inventory")
async def inventory(inter, user: discord.User = None):
    data = bot.data
    user = user if user else inter.author
    r = await bot.get_inventory(user.id)
    cards = r
    if not cards:
        await inter.send("Nothing found...")
        return
    if len(cards) <= 3:
        emb = discord.Embed(title=f"{user.display_name}'s Inventory...",
                            color=0x2F3136)
        num = 1
        desc = ""
        checked = []
        for card in cards:
            if not card[0] in checked:
                sp = card[0].split(" ")
                if len(sp) == 2:
                    card = sp[0]
                    q = sp[1]
                else:
                    card = card[0]
                    q = 1
                checked.append(card[0])
                rari = bot.rare[data[card]["rarity"]]
                desc += f"**{num}. {data[card]['name']}**\n**Group**: {data[card]['group']}\n**({rari})**\n**Quantity**: {q}\n**Card ID**: {card}\n\n"
                num += 1
        emb.description = desc
        emb.set_footer(text="Page 1 of 1")
        await inter.response.send_message(embed=emb)
    elif len(cards) > 3:
        await inter.response.defer()
        embeds = []
        num = 1
        total, left_over = divmod(len(cards), 3)
        pages = total + 1 if left_over else total
        desc = ""
        mnum = 0
        for page in range(pages):
            for card in cards:
                sp = card[0].split(" ")
                if len(sp) == 2:
                    card = sp[0]
                    q = sp[1]
                else:
                    q = 1
                emb = discord.Embed(
                    title=f"{user.display_name}'s Inventory...",
                    color=0x2F3136)
                rari = bot.rare[data[card]["rarity"]]
                desc += f"**{num}. {data[card]['name']}**\n**Group**: {data[card]['group']}\n**({rari})**\n**Quantity**: {q}\n**Card ID**: {card}\n\n"
                num += 1
                mnum += 1
                if num - 1 == len(cards):
                    emb.description = desc
                    embeds.append(emb)
                    mnum = -10000000000
                if mnum == 3:
                    mnum = 0
                    emb.description = desc
                    desc = ""
                    embeds.append(emb)
        view = Menu(embeds)
        view.inter = inter
        await inter.edit_original_message(embed=embeds[0], view=view)


@bot.slash_command(
    description="Adds a card to database. Staff only command")
async def add_card(inter, name: str, rarity: commands.Range[1, 5], group: str, id,
                   pic: discord.Attachment, limited_days:int=None):
    if not inter.guild.get_role(1024579633699627028) in inter.author.roles and inter.author.id != 756018524413100114:
        return await inter.send("You don't have permissions to use this command!")
    await inter.response.defer()
    await inter.edit_original_message(
        f"Successfully added the card with ID: {id}!")
    await pic.save(f"./pics/{id}.png")
    bot.data[id] = {"name": name, "rarity": rarity, "group": group}
    await bot.add_card_data(name, group, rarity, id, limit=limited_days)


async def all_cards(inter, user_input):
    return [id for id, value in bot.data.items()]


@bot.slash_command(
    description="Deletes a card fron database. Staff only command"
)
async def delete_card(inter, id: str):
    if not inter.guild.get_role(1024579633699627028) in inter.author.roles and inter.author.id != 756018524413100114:
        return await inter.send("You don't have permissions to use this command!")
    await inter.send("Succesfully deleted")
    await bot.delete_card(id)


async def getids(inter, input: str):
    r = await bot.get_inventory(inter.author.id)
    if not r:
        return [id for id in ["Nothing found"]]
    else:
        ids = [str(card[0].split(" ")[0]) for card in r]
        return ids


@bot.slash_command()
async def show(inter):
    pass


@show.sub_command(description="Shows information about a card")
async def card(inter, id: str = commands.Param(autocomplete=getids)):
    if id == "Nothing found":
        await inter.response.send_message("You don't have any card in your inventory.")
        return
    data = bot.data
    card = id
    rari = bot.rare[data[card]["rarity"]]
    emb = discord.Embed(
        title=f"{data[card]['name']}",
        description=
        f"🌸 **Group**: {data[card]['group']}\n🌼 **Card ID**: {card}\n🍃 **Owner**: {inter.author.mention}\n({rari})",
        color=0x2F3136)
    emb.set_image(file=discord.File(f"./pics/{id}.png", "image.png"))
    emb.set_author(name=inter.author, icon_url=inter.author.avatar.url)
    await inter.send(embed=emb)

@show.sub_command(description="Shows all cards in the database")
async def all(inter):
    ids = bot.data.keys()
    data = bot.data
    embs = []
    for card in ids:
        rari = bot.rare[data[card]["rarity"]]
        emb = discord.Embed(
        title=f"{data[card]['name']}",
        description=
        f"🌸 **Group**: {data[card]['group']}\n🌼 **Card ID**: {card}\n🍃 **Owner**: {inter.author.mention}\n({rari})",
        color=0x2F3136)
        emb.set_image(file=discord.File(f"./pics/{card}.png", "image.png"))
        embs.append(emb)
    v = Menu(embs)
    v.inter = inter
    await inter.send(embed=embs[0], view=v)

@bot.slash_command(description="Takes a card from a user. Staff only command")
async def take_card(inter, user: discord.User):
    r = await bot.get_inventory(user.id)
    view = DeleteView(user.id, r)
    view.bot = bot
    await inter.send(view=view)

@bot.slash_command(description="Gift a card to your friend")
async def gift_card(inter, user: discord.User, card_id:str=commands.Param(autocomplete=getids)):
    if not inter.guild.get_role(1024979194800779324) in inter.author.roles:
        return await inter.send("You don't have permissions to use this command!")
    if card_id == "Nothing found":
        await inter.send("You don't have any card in your inventory.", ephemeral=True)
        return
    await bot.remove_cards(inter.author.id, card_id)
    await bot.insert_card(user.id, card_id)
    await inter.send(f"You successfully gifted a card ({card_id}) to {user.mention}!")


async def getallids(inter, user_input):
    return [id for id in bot.data.keys() if user_input in id ]


@bot.slash_command(description="Gives a card to anyone. Staff only command")
async def give_card(inter, user: discord.User, card_id:str=commands.Param(autocomplete=getallids)):
    if not inter.guild.get_role(1024979194800779324) in inter.author.roles:
        return await inter.send("You don't have permissions to use this command!")
    if card_id == "Nothing found":
        await inter.send("You don't have any card in your inventory.", ephemeral=True)
        return
    await bot.insert_card(user.id, card_id)
    await inter.send(f"You successfully gifted a card ({card_id}) to {user.mention}!")

@bot.slash_command(description="Play a game of Tic Tace Toe!")
async def tictactoe(inter):
    ch = random.choice((0, 1))
    await inter.response.defer()
    if ch:
        view = TicTacToeView(inter.author)
        await inter.edit_original_message("Your turn.", view=view)
        view.m = await inter.original_message()
    else:
        view = TicTacToeView(inter.author)
        await view.next_ai_move()
        await inter.edit_original_message("Your turn.", view=view)
        view.m = await inter.original_message()


@bot.slash_command()
async def favourite(inter):
    pass


keep_alive()
def setup(token):
    bot.run(token)
