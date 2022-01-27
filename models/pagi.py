from random import randint
from typing import Any, Coroutine, Dict, Union
from discord_components import (
    DiscordComponents,
    Button,
    ButtonStyle,
    Interaction,
    ActionRow,
    Select,
    SelectOption,
)
from discord_components.dpy_overrides import ComponentMessage
from typing import List
from discord import Embed, Message, Guild
from asyncio import as_completed
from asyncio import TimeoutError as AsyncioTimeoutError
from discord.errors import NotFound


class Paginator():
    def __init__(
        self,
        client: DiscordComponents,
        send_func: Coroutine,
        contents: List[Embed],
        author_id: Any,
        values: List,
        id: int,
        forse: int,
        guild: Guild,
        t=1,
        timeout: Union[int, None]=None,
            ) -> None:
        """Пагинатор Эмбедов на кнопках

        Args:
            client (DiscordComponents): ваш клиент
            send_func (Coroutine): корутина отправки сообщения
            (channel.send | ctx.send | другое)
            contents (List[Embed]): Список включённых в пагинатор эмбедов
            author_id (Any): идентификатор для проверки,
            что именно вы нажали на кнопку
            timeout (Union[int, None], optional):
            через какое время после последнего взаимодействия
            прекратить обслуживание Defaults to None
        """
        self.__client = client
        self.__send = send_func
        self.__contents = contents
        self.__index = 0
        self.__timeout = timeout
        self.__length = len(contents)
        self.__author_id = author_id
        self.__values = values
        self.__id = str(id)
        self.__prosessed = []
        self.guild = guild
        self.forse = forse
        self.type = t
        self.check = lambda i: i.user.id == self.__author_id and i.custom_id.startswith(self.__id)
        self.__l = len(values)

    async def get_current(self):
        if len(self.__prosessed) - 1 >= self.__index:
            return self.__prosessed[self.__index]
        else:
            embed = self.__contents[self.__index]
            embed.set_thumbnail(url=self.guild.icon_url)
            for i in range(self.__index * self.forse, min(self.__l, self.__index * self.forse + self.forse)):
                try:
                    m = await self.guild.fetch_member(int(self.__values[i]['_id']))
                    m = m.display_name
                except NotFound:
                    m = 'неизвестный'
                if self.type == 1:
                    embed.add_field(name=f"`{i + 1}` | {m} | {self.__values[i]['custom']}", value=f"Уровень: `{self.__values[i]['level']}`, опыта `{self.__values[i]['exp']}`", inline=False)
                else:
                    embed.add_field(name=f"`{i + 1}` | {m} | {self.__values[i]['custom']}", value=f"Счёт: `{self.__values[i]['money']}$`", inline=False)
            self.__prosessed.append(embed)
            return embed

    async def get_components(self):
        current = await self.get_current()
        return [[
            Button(style=ButtonStyle.blue, emoji="◀️", custom_id=self.__id + "l"),
            Button(
                label=f"Страница {self.__index + 1}/{self.__length}",
                disabled=True,
                custom_id=self.__id + "c"),
            Button(style=ButtonStyle.blue, emoji="▶️", custom_id=self.__id + "r")
        ]]

    async def send(self):
        aws = [
            self.__send(
                embed=await self.get_current(),
                components=await self.get_components()
            ),
            self.__pagi_loop()
        ]
        
        res = {}
        
        for coro in as_completed(aws):
            r = await coro
            if r is not None:
                return r

    async def __pagi_loop(self) -> None:
        while True:
            try:
                interaction = await self.__client.wait_for(
                    "button_click",
                    timeout=self.__timeout
                )
            except AsyncioTimeoutError:
                return
            else:
                if self.check(interaction):
                    if interaction.custom_id == self.__id + "l":
                        self.__index = (self.__index - 1) % self.__length
                    elif interaction.custom_id == self.__id + "r":
                        self.__index = (self.__index + 1) % self.__length
                    await self.__button_callback(interaction)

    async def __button_callback(self, inter: Interaction, retr=1):
        try:
            await inter.respond(
                type=7,
                embed=await self.get_current(),
                components=await self.get_components()
            )
        except NotFound:
            if retr >= 1:
                await self.__button_callback(inter, retr=retr-1)
