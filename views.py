import disnake as discord

class CardButton(discord.ui.Button):
    
    def __init__(self, emoji, value, rarity, name, card):
        super().__init__(style=discord.ButtonStyle.blurple, emoji=emoji)
        self.value = value
        self.rarity = rarity
        self.claimed = None
        self.name = name
        self.card = card

    async def callback(self, inter):
        if inter.author==self.claimed or (inter.author in self.view.clicked):
            await inter.response.send_message(
                "You have already picked a card!", ephemeral=True)
        elif not self.claimed:
            await inter.response.send_message(
                f"You picked the #{self.value} Card!", ephemeral=True)
            self.claimed = inter.author
            self.view.clicked.append(inter.author)
            await self.view.bot.insert_card(inter.author.id, self.card)
        else:
            await inter.response.send_message("Someone has already picked this Card!", ephemeral=True)


class Cards(discord.ui.View):

    def __init__(self, rarities, names, cards):
        super().__init__(timeout=20)
        self.clicked = []
        for i, j in enumerate(["1️⃣", "2️⃣", "3️⃣"]):
            self.add_item(CardButton(j, i + 1, rarities[i], names[i], cards[i]))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        m = await self.inter.original_message()
        m.embeds[0].set_footer(text="This drop has expired")
        await self.inter.edit_original_message(view=self, embed=m.embeds[0], attachments=[])
        m = await self.inter.original_message()
        e = discord.Embed(
            title="Results of the Drop!",
            color=0x2F3136
        )
        for item in self.children:
            claimed = item.claimed.mention if item.claimed else "No one."
            e.add_field(name=f"Card #{item.value}", value=f"{item.name}\n{self.bot.rare[item.rarity]}\n\n{claimed}")
        await m.reply(embed=e)


class Menu(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=30)
        self.embeds = embeds
        self.index = 0

        # Sets the footer of the embeds with their respective page numbers.
        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {i + 1} of {len(self.embeds)}")

        self._update_state()

    def _update_state(self) -> None:
        self.first_page.disabled = self.prev_page.disabled = self.index == 0
        self.last_page.disabled = self.next_page.disabled = self.index == len(self.embeds) - 1
        self.remove.label = f"Page {self.index + 1}"

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.blurple)
    async def first_page(self, button: discord.ui.Button, inter: discord.MessageInteraction):
        self.index = 0
        self._update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self,)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev_page(self, button: discord.ui.Button, inter: discord.MessageInteraction):
        self.index -= 1
        self._update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self,)

    @discord.ui.button(label="Page 1", style=discord.ButtonStyle.grey, disabled=True)
    async def remove(self, button: discord.ui.Button, inter: discord.MessageInteraction):
        pass

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next_page(self, button: discord.ui.Button, inter: discord.MessageInteraction):
        self.index += 1
        self._update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self,)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.blurple)
    async def last_page(self, button: discord.ui.Button, inter: discord.MessageInteraction):
        self.index = len(self.embeds) - 1
        self._update_state()
        await inter.response.edit_message(embed=self.embeds[self.index], view=self,)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.inter.edit_original_message(view=self)


class DeleteView(discord.ui.View):
    def __init__(self, user_id, cards):
        super().__init__(timeout=60)
        self.remove_item(self.more)
        self.remove_item(self.one)
        self.add_item(DeleteSelect(cards))
        self.user = user_id
        self.card = None
        self.q = None


    @discord.ui.button(label="Take Single", style=discord.ButtonStyle.green)
    async def one(self, button, inter):
        await self.bot.remove_cards(self.user, self.card)
        self.clear_items()
        await inter.response.edit_message(f"Deleted a single duplicate of selected card ({self.card}) from user's inventory.", view=self)

    
    @discord.ui.button(label="Take all", style=discord.ButtonStyle.red)
    async def more(self, button, inter):
        await self.bot.remove_cards(self.user, self.card, self.q)
        self.clear_items()
        await inter.response.edit_message(f"Deleted all duplicates of selected card ({self.card}) from user's inventory.", view=self)


class DeleteSelect(discord.ui.Select):
    def __init__(self, cards):
        self.cards = cards
        options = []
        for c in cards:
            options.append(discord.SelectOption(
                label = c[0].split(" ")[0]
            ))
        super().__init__(
            placeholder="Select the card to remove...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, inter):
        for c in self.cards:
            if c[0].split(" ")[0] == self.values[0]:
                self.view.q = int(c[0].split(" ")[1])
                print(self.view.q)
        self.view.card = self.values[0]
        self.view.add_item(self.view.one)
        self.view.add_item(self.view.more)
        self.view.remove_item(self)
        await inter.response.edit_message("Do you want to take all duplicates of selected card or single one?", view=self.view)
            
            