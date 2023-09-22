"""
Файл с структурами
"""

from collections import namedtuple
from typing import NamedTuple, List, Dict

# Тип с форматом предмета из магазина
Item = NamedTuple("Item", [('name', str), ('cost', int), ('description', str), ('roles', list)])
item: Item = namedtuple('Item', ['name', 'cost', 'description', 'roles'])
# Функция для получения айди магазина по айди гильдии, лучше везде использовать её
# В базе данных хранится в поле _id
shop_id = lambda guild_id: -guild_id
# Айди аукциона
ah_id = shop_id

def get_shop(guild_id: int) -> Dict[str, List[Item]]:
    """
    Функция для получения данных о пустом магазине в гильдии
    Используется для создания записи магазина при его отсутствии/присоединении к гильдии/команде reset

    Аргументы:
        guild_id: int - айди гильдии
    """
    return {
        '_id': shop_id(guild_id),
        'guild_id': guild_id,
        'items': [],
        'ah': [],
        'rods': []
    }
