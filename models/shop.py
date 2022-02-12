from collections import namedtuple
from typing import NamedTuple, List, Dict

Item = NamedTuple("Item", [('name', str), ('cost', int), ('description', str), ('roles', list)])
item: Item = namedtuple('Item', ['name', 'cost', 'description', 'roles'])
shop_id = lambda guild_id: -guild_id
ah_id = shop_id

def get_shop(guild_id: int) -> Dict[str, List[Item]]:
    return {
        '_id': shop_id(guild_id),
        'guild_id': guild_id,
        'items': [],
        'ah': [],
        'rods': []
    }
