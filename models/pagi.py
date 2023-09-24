"""
Файл, содержащий пагинатор для работы команд scoreboard, godboard
"""

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
        t: int=1,
        timeout: Union[int, None]=None,
            ) -> None:
        """
        Пагинатор Эмбедов на кнопках

        Отличается от пагинатора из модуля paginator тем, что в данной реализации поля Embed-ов формируются по нажатию кнопок и кэшируются
        Причина: Пользователь на сервере из 100 пользователь захотел посмотреть топ 20 пользователей, следовательно остальные 80 останутся в тени
        Бот не хранит имена пользователей гильдии, только id.
        Для получения каждого отдельного имени пользователя необходимо отправить запрос в discord
        Таким образом, вместо отправки 100 запросов будет отправлено лишь 20

        Аргументы:
            client (DiscordComponents): клиент DiscordComponents
            send_func (Coroutine): корутина отправки сообщения
            (channel.send | ctx.send | другое)
            contents (List[Embed]): список включённых в пагинатор эмбедов
            author_id (Any): идентификатор для проверки,
            что именно пользователь, который вызвал команду нажал на кнопку
            values (List[Any]): список данных, необходимых для формирования каждого элемента, используется упорядоченность
            (Обычно - список словарей с данными о пользователе, см. приминение в get_current)
            id (int): уникальный идентификатор пагинатора, используется для формирования custom_id компонентов (кнопок, селекта),
            чтобы можно было разобрать поступающие от сервера interaction-ы и определить, к какой кнопке они относятся
            forse (int): количество элементов на странице
            guild (Guild): объект гильдии
            t: int - тип пагинатора (1 - scoreboard, не 1 - godboard)
            timeout (Union[int, None]): опционально
            через какое время в секундах после последнего взаимодействия
            прекратить обслуживание
        """
        self.__client = client
        self.__send = send_func
        self.__contents = contents
        self.__index = 0
        self.__timeout = timeout
        # Количество embed-ов
        self.__length = len(contents)
        self.__author_id = author_id
        self.__values = values
        self.__id = str(id)
        # Список кэшированных Embed-ов
        self.__prosessed = []
        self.guild = guild
        self.forse = forse
        self.type = t
        # Функция проверки custom_id объекта Interaction на предмет отношения к данному объекту пагинатора
        self.check = lambda i: i.user.id == self.__author_id and i.custom_id.startswith(self.__id)
        # Количество элементов на всех страницах
        self.__l = len(values)

    async def get_current(self):
        """
        Метод получения текущего наполнения embed-а
        Если страница ещё не была отображена, будет запрощена информация от discord
        Иначе будет возвращён кэшированный embed

        Возвращает:
            embed: Embed - готовый для отправки Embed, с полями, соответствующими текущему номеру страницы
        """
        if len(self.__prosessed) - 1 >= self.__index:
            # Embed уже кэширован
            return self.__prosessed[self.__index]
        else:
            # нужно подготовить ещё не отображённый Embed
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
        """
        Метод получения компонентов для embed-а

        Возвращает:
            List[component] - список компонентов
        """
        return [[
            Button(style=ButtonStyle.blue, emoji="◀️", custom_id=self.__id + "l"),
            Button(
                label=f"Страница {self.__index + 1}/{self.__length}",
                disabled=True,
                custom_id=self.__id + "c"),
            Button(style=ButtonStyle.blue, emoji="▶️", custom_id=self.__id + "r")
        ]]

    async def send(self):
        """
        Главный метод пагинатора, формирует список задач, которые нужно асинхронно одновременно выполнять
        и запускает их обработчик

        Возвращает:
            m: Message - объект отправленного пагинатора
        """
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
        """
        Цикл обработки пагинации
        """
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
        """
        Обработчик нажатия кнопок '<' и '>'
        
        Аргументы:
            inter: Interaction - объект взаимодействия
            retr: int - количество попыток повторной отправки ответа на взаимодействие (если сообщение не удалось найти с первой попытки)
            по умолчанию - 1, считается оптимальным
        """
        try:
            await inter.respond(
                type=7,
                embed=await self.get_current(),
                components=await self.get_components()
            )
        except NotFound:
            if retr >= 1:
                await self.__button_callback(inter, retr=retr-1)
