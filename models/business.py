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

BUSINESS = namedtuple("BUSINESS", ['id', 'action_name', 'name', 'description', 'cost', 'stock'])

FISH_PRESERVES_FACTORY: BUSINESS = BUSINESS(0, "Консервировать", 'Завод рыбных консервов', 'Перерабатывайте рыбу за её стоимость в компонентах и продавайте её за `x 2.5` от стоимости', [(components['1'], 1000), (components['2'], 1000),(components['3'], 1000), (components['4'], 1000), (components['5'], 1000), (components['6'], 1000), (components['7'], 1000), (components['8'], 1000)], False)
FISHING_SHOP: BUSINESS = BUSINESS(1, "На прилавок", 'Рыболовный магазин', 'Продайте рыбу в своём магазине за `x 1.1 от стоимости`', [(components['1'], 50), (components['2'], 50),(components['3'], 50), (components['4'], 50), (components['5'], 50), (components['6'], 50), (components['7'], 50), (components['8'], 50)], True)
RED_BOOK_RESELL: BUSINESS = BUSINESS(2, "Продать экологам", "Контракт с экологами", "Заключите контракт с экологами и продавайте им самых редких рыб [Лосось, Золотая, Язь] за `x 2` от стоимости, может сочетаться с рыболовным магазином", [(components['1'], 200), (components['2'], 200),(components['3'], 200), (components['4'], 200), (components['5'], 200), (components['6'], 200), (components['7'], 200), (components['8'], 200)], True)

BUSINESSES: Dict[int, BUSINESS] = {
    0 : FISH_PRESERVES_FACTORY,
    1 : FISHING_SHOP,
    2 : RED_BOOK_RESELL
}

SUCCESS = 1
NOT_ENOUGH_COMPONENTS = 2

async def conserve(fish):
    return fish()

async def logic(business: BUSINESS, fish: fish, guild_id, user_id):
    if business is FISH_PRESERVES_FACTORY:
        return await conserve(guild_id, user_id, fish)
    
class Business():
    async def conserve(self, fish_cost, fish_components, user_components):
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
        inc = int(fish.cost * 1.1)
        return {'$inc': {'money': inc}}, f"`{fish.cost} + {int(fish.cost * 0.1)}`"
    
    
    async def genEmbed(self, b: BUSINESS, success: bool, income=None):
        if b is FISH_PRESERVES_FACTORY:
            if success:
                return Embed(title=f"Рыба законсервирована и продана за {income}", color=Colour.dark_theme())
            else:
                return Embed(title="Недостаточно компонентов для консервации", color=Colour.dark_theme())
        elif b is FISHING_SHOP:
            return Embed(title=f"Кто-то купил рыбу с вашего прилавка, ваша прибыль: {income}", color=Colour.dark_theme())
    
    async def logic(self, b: BUSINESS, guild_id: int, user_id: int, fish_components, fish_cost, user_components: dict) -> Embed:
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
    
    async def sell(self, businesses: List[int], fish_cost, fish_name):
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