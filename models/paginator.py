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
from discord import Embed, Message
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
        self.forse = forse
        self.check = lambda i: i.user.id == self.__author_id and i.custom_id.startswith(self.__id)


    async def get_current(self):
        e = self.__contents[self.__index]
        v = self.__values[self.__index * self.forse: min(self.__index * self.forse + self.forse, len(self.__values))]
        return [{'label': e.fields[i].name, 'value': v[i]} for i in range(len(e.fields))]

    async def get_components(self):
        current = await self.get_current()
        return [[
            Button(style=ButtonStyle.blue, emoji="◀️", custom_id=self.__id + "l"),
            Button(
                label=f"Страница {self.__index + 1}/{self.__length}",
                disabled=True,
                custom_id=self.__id + "c"),
            Button(style=ButtonStyle.blue, emoji="▶️", custom_id=self.__id + "r")
        ], [
            Select(
            placeholder='Выберите товар',
            options=[*[SelectOption(label=i['label'], value=i['value']) for i in current], SelectOption(label="Отменить", value='Отменить')]
            ,custom_id=self.__id + "s")
        ]]

    async def send(self):
        aws = [
            self.__send(
                embed=self.__contents[self.__index],
                components=await self.get_components()
            ),
            self.__pagi_loop(),
            self.__select_loop()
        ]
        
        res = {}
        
        for coro in as_completed(aws):
            r = await coro
            if r is not None:
                if isinstance(r, ComponentMessage):
                    res['message'] = r
                elif r == 0:
                    res['interaction'] = r
                else:
                    res['interaction'] = r
                if len(res) >= 2:
                    return res["interaction"].values[0] if res["interaction"] != 0 else None, res["interaction"], res["message"]

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
    
    async def __select_loop(self) -> None:
        while True:
            try:
                interaction = await self.__client.wait_for(
                    "select_option",
                    timeout=self.__timeout
                )
            except AsyncioTimeoutError:
                return 0
            else:
                if self.check(interaction):
                    return interaction

    async def __button_callback(self, inter: Interaction, retr=1):
        try:
            await inter.respond(
                type=7,
                embed=self.__contents[self.__index],
                components=await self.get_components()
            )
        except NotFound:
            if retr >= 1:
                await self.__button_callback(inter, retr=retr-1)
