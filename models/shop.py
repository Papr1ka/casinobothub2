from collections import namedtuple
from typing import NamedTuple, List, Dict

Item = NamedTuple("Item", [('name', str), ('cost', int), ('description', str), ('roles', list)])
item: Item = namedtuple('Item', ['name', 'cost', 'description', 'roles'])
shop_id = -1
ah_id = -1

def get_shop(guild_id: int) -> Dict[str, List[Item]]:
    return {
        '_id': -1,
        'guild_id': guild_id,
        'items': [],
        'ah': [],
        'rods': []
    }
