"""
Файл, описывающий инструменты для поддержки работы бизнеса при рыбалке
"""

from collections import namedtuple
from typing import Dict, List
from models.fishing import fish
from database import db
from discord import Embed, Colour
from handlers import MailHandler
from logging import config, getLogger
from models.fishing import components

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())

# Тип бизнеса
BUSINESS = namedtuple("BUSINESS", [
    'id', # айди бизнеса, int
    'action_name', # название кнопки взаимодействия, str
    'name', # название бизнеса
    'description', # описание бизнеса
    'cost', # стоимость бизнеса в компонентах, List[Tuple(component, int)] - список кортежей, где 1-й элемент - компонент, второй - его количество
    'stock' # наличие возможности работы бизнеса из садка (кнопка консервировать для завода рыбных консервов)
])

# Завод рыбных консервов
FISH_PRESERVES_FACTORY: BUSINESS = BUSINESS(0, "Консервировать", 'Завод рыбных консервов', 'Перерабатывайте рыбу за её стоимость в компонентах и продавайте её за `x 2.5` от стоимости', [(components['1'], 1000), (components['2'], 1000),(components['3'], 1000), (components['4'], 1000), (components['5'], 1000), (components['6'], 1000), (components['7'], 1000), (components['8'], 1000)], False)
# Рыболовный магазин
FISHING_SHOP: BUSINESS = BUSINESS(1, "На прилавок", 'Рыболовный магазин', 'Продайте рыбу в своём магазине за `x 1.1 от стоимости`', [(components['1'], 50), (components['2'], 50),(components['3'], 50), (components['4'], 50), (components['5'], 50), (components['6'], 50), (components['7'], 50), (components['8'], 50)], True)
# Контракт с экологами
RED_BOOK_RESELL: BUSINESS = BUSINESS(2, "Продать экологам", "Контракт с экологами", "Заключите контракт с экологами и продавайте им самых редких рыб [Лосось, Золотая, Язь] за `x 2` от стоимости, может сочетаться с рыболовным магазином", [(components['1'], 200), (components['2'], 200),(components['3'], 200), (components['4'], 200), (components['5'], 200), (components['6'], 200), (components['7'], 200), (components['8'], 200)], True)

# Все существующие бизнесы
BUSINESSES: Dict[int, BUSINESS] = {
    0 : FISH_PRESERVES_FACTORY,
    1 : FISHING_SHOP,
    2 : RED_BOOK_RESELL
}

SUCCESS = 1
NOT_ENOUGH_COMPONENTS = 2
    
class Business():
    """
    Инструментарий для работы бизнеса
    """
    async def conserve(self, fish_cost: int, fish_components: list, user_components: list):
        """
        Метод, 'консервирующий' рыбу за её стоимость в компонентах, владелец бизнеса получает стоимость рыбы с коэффициентом 2.5

        Ключ бизнеса в словаре BUSINESSES - 0

        Аргументы:
            fish_cost: int - стоимость рыбы в деньгах
            fish_components: Dict[component_id: str, amount: int]  - стоимость рыбы в компонентах, component_id - ключ компонента для словаря components, amount - его количество
            user_components: Dict[component_id: str, amount: int]  - компоненты пользователя, component_id - ключ компонента для словаря components, amount - его количество
        
        Возвращает:
            query: dict | None - словарь, содержащий запрос на обновление информации о пользователе в базе данных,
            income: str | None - строка формирования итоговой цены продажи рыбы 
        """
        can_pay = True
        
        for comp, col in fish_components.items():
            try:
                if user_components[comp] < col:
                    can_pay = False
                    break
            except KeyError:
                can_pay = False
                break
        if can_pay:
            comps = {f'finventory.components.{comp}': -col for comp, col in fish_components.items()}
            inc = int(fish_cost * 2.5)
            return {'$inc': {'money': inc, **comps}}, f"`{fish_cost} + {int(fish_cost * 1.5)}$`"
        else:
            return None, None
    
    async def sell_shop(self, fish: fish):
        """
        Метод, продающий рыбу в 'собственном магазине', владелец бизнеса продаёт рыбу за её стоимость с коэффициентом 1.1

        Ключ бизнеса в словаре BUSINESSES - 1

        Аргументы:
            fish: fish - продаваемая рыба
        
        Возвращает:
            dict - словарь, содержащий запрос на обновление информации о пользователе в базе данных
        """
        inc = int(fish.cost * 1.1)
        return {'$inc': {'money': inc}}, f"`{fish.cost} + {int(fish.cost * 0.1)}`"
    
    
    async def genEmbed(self, b: BUSINESS, success: bool, income: str=None):
        """
        Метод возвращает нужный Embed в зависимости от типа бизнеса, поясняющий пользователю то, как отработал бизнес,
        вызывается после работы основной логики бизнса (после метода logic)

        Аргументы:
            b: BUSINESS - тип бизнеса
            success: bool - успешно ли отработал бизнес
            income: str | None - строка формирования итоговой стоимости
        
        Возвращает:
            embed: Embed - сформированный Embed
        """
        if b is FISH_PRESERVES_FACTORY:
            if success:
                return Embed(title=f"Рыба законсервирована и продана за {income}", color=Colour.dark_theme())
            else:
                return Embed(title="Недостаточно компонентов для консервации", color=Colour.dark_theme())
        elif b is FISHING_SHOP:
            return Embed(title=f"Кто-то купил рыбу с вашего прилавка, ваша прибыль: {income}", color=Colour.dark_theme())
    
    async def logic(self, b: BUSINESS, guild_id: int, user_id: int, fish_components: list, fish_cost: int, user_components: dict) -> Embed:
        """
        Метод, вызывается при нажатии кнопки бизнеса (Пример - консервировать), обрабатывает действие бизнеса
        (делает всё необходимое, включая запись в базу данных), возвращает Embed и состояние

        Аргументы:
            b: BUSINESS - тип бизнеса
            guild_id: int - айди гильдии
            user_id: int - айди пользователя
            fish_components: Dict[component_id: str, amount: int] - набор компонентов рыбы,
            component_id - ключ компонента для словаря components, amount - количество компонента
            fish_cost: int - стоимость рыбы
            user_components: Dict[component_id: str, amount: int] - компоненты пользователя,
            component_id - ключ компонента для словаря components, amount - количество компонента
        
        Возвращает:
            embed: Embed, status: int - embed - сообщение о результате работы бизнеса,
            status: int | None - успешно/ошибка (1 - успешно, 2 - недостаточно компонентов)
        """
        if b is FISH_PRESERVES_FACTORY:
            r, income = await self.conserve(fish_cost, fish_components, user_components)
            if not r is None:
                await db.update_user(guild_id, user_id, r)
                return await self.genEmbed(FISH_PRESERVES_FACTORY, True, income=income), SUCCESS
            else:
                return await self.genEmbed(FISH_PRESERVES_FACTORY, False), NOT_ENOUGH_COMPONENTS
        else:
            logger.error("InvalidBusiness")
            return Embed(title="Что-то пошло не так", color=Colour.dark_theme)
    
    async def sell(self, businesses: List[int], fish_cost: int, fish_name: int):
        """
        Метод, возвращающий итоговую цену продажи рыбы с учётом всех имеющихся бизнесов

        Аргументы:
            businesses: List[int] - список ключей бизнесов
            fish_cost: int - исходная цена рыбы
            fish_name: int - цена рыбы
        
        Возвращает:
            cost: int, pretty: str - цена рыбы с учётом бонусов бизнеса, строка формирования цены
            Пример: Лосось за 850$, купленные бизнесы - [1, 2], Вернёт - (1785, '850 + 85 + 850$'),
        """
        cost = fish_cost
        pretty = str(fish_cost)
        for i in businesses:
            if i is FISHING_SHOP.id:
                inc = int(cost * 0.1)
                cost += inc
                pretty += " + " + str(inc)
            elif i is RED_BOOK_RESELL.id:
                if fish_name in ("Лосось", "Золотая", "Язь"):
                    inc = fish_cost
                    cost += inc
                    pretty += " + " + str(inc)
        return cost, pretty
            

B = Business()