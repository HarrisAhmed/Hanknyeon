from disnake.ext import commands
import asqlite
import disnake
from datetime import date

class Hanknyeon(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="..",
            intents=disnake.Intents.all(),
            test_guilds=[1024399481782927511, 1024402764601765978],
            status=disnake.Status.idle,
            activity=disnake.Game("with JoyStick")
        )
        self.conn: asqlite.Connection = None
        self.data = {}
        self.rare = {
    1:"✿❀❀❀❀",
    2:"✿✿❀❀❀",
    3:"✿✿✿❀❀",
    4:"✿✿✿✿❀",
    5:"✿✿✿✿✿"
}
        
    async def get_inventory(self, user_id):
            async with self.conn.cursor() as cursor:
                await cursor.execute("CREATE TABLE IF NOT EXISTS CARDS(user_id INT, cards TEXT)")
                await cursor.execute("SELECT cards from CARDS WHERE user_id=?", (user_id,))
                r = await cursor.fetchall()
                await self.conn.commit()
                return r
                
            
    async def insert_card(self, user_id, card):
            async with self.conn.cursor() as cursor:
                await cursor.execute("CREATE TABLE IF NOT EXISTS CARDS(user_id INT, cards TEXT)")
                await cursor.execute("SELECT cards from CARDS WHERE user_id=?", (user_id,))
                r = await cursor.fetchall()
                if r:
                    for cards in r:
                        c = cards[0][:8]
                        if c == card:
                            card = f"{card} {int(cards[0][9:])+1}"
                            await cursor.execute("UPDATE CARDS SET cards=? WHERE user_id=? AND cards=?", (card, user_id, cards[0]))
                            await self.conn.commit()
                            return
                card = card + " 1"
                await cursor.execute("INSERT INTO CARDS(user_id, cards) VALUES(?,?)", (user_id, card))
                await self.conn.commit()

    async def add_card_data(self, name, grop, rarity, id, limit):
            async with self.conn.cursor() as cursor:
                if limit:
                    print("here")
                    EndDate = date.today()
                    name = name + f" (Limited till {EndDate})"
                    await cursor.execute("CREATE TABLE IF NOT EXISTS LIMITED(card TEXT, date DATE)")
                    await cursor.execute("INSERT INTO LIMITED(card, date) VALUES(?, ?)", (id, EndDate))
                await cursor.execute("CREATE TABLE IF NOT EXISTS CARDS_DATA(name, grop, rarity INT,ID)")
                await cursor.execute("INSERT INTO CARDS_DATA(name, grop, rarity, ID) VALUES(?, ?, ?, ?)", (name, grop, rarity, id))
                await self.conn.commit()
                self.data[id] = {"name":name, "group":grop, "rarity":rarity}

    def sort_time(self, s):
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        time_dict = {int(w):" week", int(d):" day", int(h):" hour", int(m):" minute", int(s):" second"}
        for item in time_dict.keys():
            if int(item) > 1:
                time_dict[item] = time_dict[item] + "s"
        return " ".join(str(i) + k for i, k in time_dict.items() if i!=0)
    
    async def get_cards_data(self):
            async with self.conn.cursor() as cursor:
                await cursor.execute("CREATE TABLE IF NOT EXISTS CARDS_DATA(name, grop, rarity INT,ID)")
                await cursor.execute("SELECT * from CARDS_DATA")
                r = await cursor.fetchall()
                for cards in r:
                    self.data[cards[3]] = {"name":cards[0], "rarity":cards[2], "group":cards[1]}

    async def delete_card(self, id, limit=False):
            async with self.conn.cursor() as cursor:
                name = f"{self.data[id]['name']} (Not Accessible)"
                await cursor.execute("UPDATE CARDS_DATA SET name=? WHERE id=?",(name, id))
                self.data[id]["name"] = name
                await self.conn.commit()
                if limit:
                    await cursor.execute("DELETE FROM LIMITED WHERE card=?", (id))
                    await self.conn.commit()

    async def limited_cards(self):
        async with self.conn.cursor() as cursor:
            await cursor.execute("CREATE TABLE IF NOT EXISTS LIMITED(card TEXT, date DATE)")
            await cursor.execute("SELECT * FROM LIMITED")
            r = await cursor.fetchall()
            return r
    
    async def remove_cards(self, user_id, card, num=1):
            async with self.conn.cursor() as cursor:
                await cursor.execute("SELECT cards from CARDS WHERE user_id=?", (user_id,))
                r = await cursor.fetchall()
                for c in r:
                    if c[0].startswith(card):
                        n = int(c[0].split(" ")[1])
                        if n-num == 0:
                            await cursor.execute("DELETE FROM CARDS WHERE user_id=? AND cards=?", (user_id, c[0],))
                            await self.conn.commit()
                        else:
                            card = c[0].split(" ")[0] + " " + str(n-num)
                            await cursor.execute("UPDATE CARDS SET cards=? WHERE user_id=? AND cards=?", (card, user_id, c[0]))
                            await self.conn.commit()

    async def insert_profile(self, user_id, created=None, fav=None):
        async with self.conn.cursor() as cursor:
            await cursor.execute("CREATE TABLE IF NOT EXISTS profile(user_id TEXT, dt TEXT, fav TEXT)")
            await cursor.execute("INSERT INTO profile()")