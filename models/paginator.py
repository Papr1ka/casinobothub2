"""
Файл, содержащий пагинатор для работы команд shop, fsop, cage, workshop, inventory market, rods, business
"""

from typing import Any, Coroutine, Union
from discord_components import (
    DiscordComponents,
    Button,
    ButtonStyle,
    Interaction,
    Select,
    SelectOption,
)
from discord_components.dpy_overrides import ComponentMessage
from typing import List
from discord import Embed
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
        select_opts = []
            ) -> None:
        """
        Пагинатор Эмбедов на кнопках

        Отличается от пагинатора из модуля pagi тем, что в данной реализации подразумевается,
        что все поля embed-ов заранее определены и получение дополнительной информации не требуется
        в реализации из модуля pagi Embed формируется по нажатию кнопки и кэшируется

        Аргументы:
            client (DiscordComponents): клиент DiscordComponents
            send_func (Coroutine): корутина отправки сообщения
            (channel.send | ctx.send | другое)
            contents (List[Embed]): список включённых в пагинатор эмбедов
            author_id (Any): идентификатор для проверки,
            что именно пользователь, который вызвал команду нажал на кнопку
            values (List[Any]): список уникальных значений, каждое из которых соответствует опции выбора,
            (Пояснение - пусть в магазине сервера 30 позиций, значит должно быть 30 разных параметров в списке values)
            при выборе товара вернётся его уникальное значение, по которому можно будет определить, что за товар выбран,
            обычно в values поступает список номеров элементов ([0, 1, ..., 29]) 
            id (int): уникальный идентификатор пагинатора, используется для формирования custom_id компонентов (кнопок, селекта),
            чтобы можно было разобрать поступающие от сервера interaction-ы и определить, к какой кнопке они относятся
            forse (int): количество элементов на странице
            timeout (Union[int, None]): опционально
            через какое время в секундах после последнего взаимодействия
            прекратить обслуживание
            select_opts (List[SelectOption]): список опций выбора, отображаемых на каждой странице
            (Пример - Продать всё, Разобрать всё в команде cage)
        """
        self.__client = client
        self.__send = send_func
        self.__contents = contents
        # Текущий индекс страницы
        self.__index = 0
        self.__timeout = timeout
        # Количество embed-ов
        self.__length = len(contents)
        self.__author_id = author_id
        self.__values = values
        self.__id = str(id)
        self.forse = forse
        # Функция проверки custom_id объекта Interaction на предмет отношения к данному объекту пагинатора
        self.check = lambda i: i.user.id == self.__author_id and i.custom_id.startswith(self.__id)
        self.select_opts = select_opts


    async def get_current(self):
        """
        Метод получения текущего наполнения embed-а

        Возвращает:
            List[Dict[str, str]] - список словарей с полями
            label: str - название опции выбора
            value: str - уникальное значение опции выбора
        """
        e = self.__contents[self.__index]
        v = self.__values[self.__index * self.forse: min(self.__index * self.forse + self.forse, len(self.__values))]
        return [{'label': e.fields[i].name, 'value': v[i]} for i in range(len(e.fields))]

    async def get_components(self):
        """
        Метод получения компонентов для embed-а

        Возвращает:
            List[component] - список компонентов
        """
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
            options=[*[SelectOption(label=i['label'], value=i['value']) for i in current], SelectOption(label="Отменить", value='Отменить'), *[i for i in self.select_opts]]
            ,custom_id=self.__id + "s")
        ]]

    async def send(self):
        """
        Главный метод пагинатора, формирует список задач, которые нужно асинхронно одновременно выполнять
        и запускает их обработчик

        Возвращает:
            (response: Any, inter: Interaction, msg: Message) | None, None, None
            response: уникальное значение опции выбора
            inter - объект взаимодействия
            msg - объект отправленного сообщения (пагинатора)
        """
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
    
    async def __select_loop(self) -> None:
        """
        Цикл обработки опции выбора

        Возвращает:
            r: int | Interaction - объект взаимодействия или 0, если превышен лимит ожидания
        """
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

    async def __button_callback(self, inter: Interaction, retr: int=1):
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
                embed=self.__contents[self.__index],
                components=await self.get_components()
            )
        except NotFound:
            if retr >= 1:
                await self.__button_callback(inter, retr=retr-1)
