from collections import namedtuple
from random import uniform, choice
from typing import Dict, List, Union

fish_rod = namedtuple('Fish_rod', ['name', 'cost', 'description', 'modifiers', 'url', 'id'])
pond = namedtuple('Pond', ['name', 'cost', 'description', 'modifiers', 'url', 'id'])
fish = namedtuple('Fish', ['name', 'cost', 'description', 'url', 'weight', 'components'])
fish_chance = namedtuple('FishChance', ['id', 'chance'])
MarketFish = namedtuple("MarketFish", ['name', 'cost', 'description', 'url', 'weight', 'components', 'seller', 'sellcost', 'sellername', 'id'])
component = namedtuple('Component', ['name', 'id', 're'])
box = namedtuple('Box', ['name', 'cost', 'description', 'loot', 'url', 'tier'])

components: Dict[int, component] = {
    "1": component('Бамбук', "1", 'BA'),
    "2": component('Карбон', "2", 'CA'),
    "3": component('Композит', "3", 'CO'),
    "4": component('Керамика', "4", 'CE'),
    "5": component('Алюминий', "5", "AL"),
    "6": component('Графит', "6", "GR"),
    "7": component('Нейлон', "7", "NY"),
    "8": component('Капрон', "8", "KA"),
}

rods: Dict[int, fish_rod] = {
    1: fish_rod('Бамбук', 1000, "Сделана из подручных материалов", {'x': 1, 'aim': 1}, "https://i.ibb.co/dDXVT8j/image.png", 1),
    2: fish_rod('Ручейник', 5000, "Удилище выполнено из покрашеного бамбука, нейлоновая леска малозаметна в воде", {'x': 1.2, 'aim': 1}, "https://i.ibb.co/Hq7TnrS/image.png", 2),
    3: fish_rod('Белимер', 25000, "Отборный бамбук, композитная ручка, графитовая катушка", {'x': 1.5, 'aim': 1}, "https://i.ibb.co/p0nnkZL/image.png", 3),
    4: fish_rod('Флеир', 50000, "Полностью исполнена из карбона, максимальная лёгкость", {'x': 1.75, 'aim': 2}, "https://i.ibb.co/6r6kcdr/image.png", 4),
    5: fish_rod('Сова', 100000, "На твоей стороне сила ночного хищника, лучше всего подходит для ночной рыбалки", {'x': 2, 'aim': 2, 'time': (0.8, 1.2)}, "https://i.ibb.co/ZX5xqj5/image.png", 5),
    7: fish_rod('Скарабей', 300000, "Технологии - народу", {'x': 3, 'aim': 3}, "https://i.ibb.co/VNRYtbG/image.png", 7),
    6: fish_rod('Удочка Миллионера', 1000000, "Изумрудная удочка непрактична? Добавьте туда алмазы!", {'x': 5, 'aim': 3}, "https://i.ibb.co/92PNTng/image.png", 6),
    8: fish_rod('Гринфайр', 10000000, "Её свет привлекает рыбу", {'x': 10, 'aim': 5}, "https://i.ibb.co/Swjtpmg/image.png", 8)
}


#id must be unicle with rods
custom_rods: Dict[int, fish_rod] = {
    1000: fish_rod("Пенак", [(components['1'], 50), (components['7'], 30)], "именно с него начинал свой путь рыбака незнакомец на обложке Престного водоёма", {'x': 1.5, 'aim': 2}, "https://i.ibb.co/JxmZLxz/image.png", 1000),
    1001: fish_rod("Танзаврида", [(components['6'], 80), (components['2'], 100), (components['7'], 300)], "Любит туман", {'x': 3, 'aim': 2, 'weather': {"🌫️ Туман": 1.25, "🌞 Ясно": 0.75, "🌧️ Дождь": 0.75}}, "https://i.ibb.co/XxHhbvy/image.png", 1001),
    1002: fish_rod("Корвина", [(components['5'], 1000), (components['3'], 400), (components['6'], 800), (components['4'], 80), (components['8'], 250)], "Выкована в кузне богов", {'x': 5, 'aim': 3}, "https://i.ibb.co/4Pt9LNF/image.png", 1002),
}

all_rods = {**rods, **custom_rods}

ponds: Dict[int, pond] = {
    1: pond("Пресный водоём", 1000, "Единственный пресный водоём в округе", {'x': 1.0, "chances": [fish_chance(2, 0.5), fish_chance(8, 0.3), fish_chance(7, 0.1), fish_chance(5, 0.08), fish_chance(1, 0.02)]}, "https://i.ibb.co/KNky44x/image.png", 1),
    2: pond("Море", 30000, "либо поймаешь ты, либо поймают тебя", {'x': 1.0, "chances": [fish_chance(3, 0.4), fish_chance(9, 0.36), fish_chance(10, 0.2), fish_chance(6, 0.03), fish_chance(4, 0.01)]}, "https://i.ibb.co/njdKhpf/image.png", 2),
    3: pond("Болото", 300000, "отличное место для рыбалки", {'x': 1.0, "chances": [fish_chance(11, 0.36), fish_chance(12, 0.36), fish_chance(13, 0.2), fish_chance(14, 0.07), fish_chance(15, 0.01)]}, "https://i.ibb.co/m9tL5pZ/image.png", 3)
}

fishs: Dict[int, fish] = {
    1: fish("Лосось", 800, "Каждый рыбак мечтает поймать эту рыбу: её средний вес 11 килограмм!", "https://i.ibb.co/71sSjPT/image.png", (1.1, 21.1, 11.1), (components["3"], components["4"])), #weight: (min, max, avg)
    2: fish("Ставрида", 100, "Имеет веретенообразное удлинённое тело, покрытое мелкой чешуёй, оканчивающееся тонким хвостовым стеблем.", "https://i.ibb.co/bdZNF0t/image.png", (1, 2, 1.5), (components["1"], )),
    3: fish("Рыба-самолёт", 150, "Это птица? это самолёт? нет! это рыба-самолёт", "https://i.ibb.co/wSkRhbV/image.png", (1, 3, 2), (components["5"], )),
    4: fish("Золотая", 2000, "В другой игре слова 'отпусти меня, старче' имели бы смысл'", "https://i.ibb.co/Tbm84zD/image.png", (1, 1.5, 1.25), (components["7"], components["4"], )),
    5: fish("Сом", 300, "Один из ценнейших трофеев рыбака", "https://i.ibb.co/7gDdtpC/image.png", (0.1, 20, 10.05), (components["6"], )),
    6: fish("Акула", 1250, "Как она вообще клюнула?!", "https://i.ibb.co/vPwRhWf/image.png", (0.2, 20000, 10000.1), (components["8"], components["3"], components["6"], components["4"])),
    7: fish("Щука", 200, "Не говорящая, но и мы не в сказке", "https://i.ibb.co/kGRKPg4/image.png", (0.1, 8, 4.05), (components["2"], )),
    8: fish("Линь", 60, "Уникальный вид, отличный вкус и стоит дёшево!", "https://i.ibb.co/bKkYvDX/image.png", (0.1, 4, 2.05), (components["7"], )),
    9: fish("Треска", 200, "Популярный трофей северных морей", "https://i.ibb.co/gSQvXgk/image.png", (0.1, 10, 5.05), (components["6"], )),
    10: fish("Палтус", 100, "В этом море они долго не живут", "https://i.ibb.co/k6yh87t/image.png", (7, 100, 53.5), (components["1"], components["4"])),
    11: fish("Карп", 200, "Ловлю карпа бывалые рыболовы сравнивают с партизанской войной, побеждает в которой тот, кто умеет думать, проявляет выдержку и изобретательность", "https://i.ibb.co/F7K2mmQ/image.png", (0.5, 4, 2.25), (components["8"], components["3"], components["6"])),
    12: fish("Карась", 300, "Является геральдическим символом богатства, справедливости, великодушия", "https://i.ibb.co/TP3JRhc/image.png", (0.1, 4.5, 2.3), (components["2"], )),
    13: fish("Окунь", 150, "В кулинарии рыба ценится за вкусное мясо и небольшое количество костей", "https://i.ibb.co/hctY1Bz/image.png", (0.1, 2.2, 1.15), (components["7"], )),
    14: fish("Ротан", 500, "Регулирует численность карася", "https://i.ibb.co/xswchBz/image.png", (0.1, 0.8, 0.45), (components["6"], components["4"])),
    15: fish("Язь", 2500, "Ценится за красоту", "https://i.ibb.co/wrpzhcr/image.png", (2, 8, 5), (components["1"], components["4"], components["8"])),
}


prise = Union[int, fish, component]

prises: Dict = {
    1: 500,
    2: components['1'],
    3: "1",
    4: (choice, list(str(i) for i in fishs.keys())),
    5: (choice, list(components.values())),
    6: 2000
}

boxes: Dict[int, box] = {
    10000: box("Бамбуковая коробка", [(components['1'], 5), (components['7'], 5)], "Деньги, бамбук, или лосось!", [fish_chance(1, 0.45), fish_chance(2, 0.45), fish_chance(3, 0.98)], "https://i.ibb.co/VmTVbwL/present1.png", 1),
    10001: box("Подарочная коробка", [(components['1'], 5), (components['2'], 5), (components['3'], 5), (components['4'], 5), (components['5'], 5), (components['6'], 5), (components['7'], 5), (components['8'], 5)], "Никто не знает, что там лежит!", [fish_chance(4, 0.33), fish_chance(5, 0.33), fish_chance(6, 0.34)], "https://i.ibb.co/Tv2qysN/present2.png", 4),
    #10002: box("Подарочная коробка", [(components['1'], 5), (components['2'], 5), (components['3'], 5)], "Никто не знает, что там лежит!", [fish_chance(4, 0.33), fish_chance(5, 0.33), fish_chance(6, 0.34)], "https://i.ibb.co/d0bKzqw/present3.png", 4),
    #10003: box("Подарочная коробка", [(components['1'], 5), (components['2'], 5), (components['3'], 5)], "Никто не знает, что там лежит!", [fish_chance(4, 0.33), fish_chance(5, 0.33), fish_chance(6, 0.34)], "https://i.ibb.co/XLndnzT/present4.png", 4),
    #10004: box("Подарочная коробка", [(components['1'], 5), (components['2'], 5), (components['3'], 5)], "Никто не знает, что там лежит!", [fish_chance(4, 0.33), fish_chance(5, 0.33), fish_chance(6, 0.34)], "https://i.ibb.co/ggjTnSM/present5.png", 4),
}

wshop = {**custom_rods, **boxes}

fishing_shop = {
    'rods': list(rods.keys()), #id fish_rod,
    'ponds': list(ponds.keys()) #id pond
}

modifiers = {
    "🌧️ Дождь": 1,
    "🌫️ Туман": 0.75,
    "🌞 Ясно": 0.85
}

temp_modifiers = {
    i: 1 if i in range(15, 21) else 0.9 if (i in range(8, 15) or i in range(21, 26)) else 0.8 for i in range(31)
}

async def get_fish(index, modifier, temp, weather, time=None, t=None, w=None):
    f = fishs[index]
    if w:
        modifier *= w[weather]
    if t:
        if time in range(21, 6):
            modifier *= t[0]
        else:
            modifier *= t[1]
    avg = f.weight[2]
    weight = round(uniform(f.weight[0], f.weight[1]), 2)
    cost = round(f.cost * weight / avg * modifier * modifiers[weather] * temp_modifiers[temp])
    comps = {
        i.id: max(1, round(weight * 2 / avg * modifier * modifiers[weather] * temp_modifiers[temp])) for i in f.components
    }
    return fish(f.name, cost, f.description, f.url, weight, comps)

async def json_fish(fish: fish):
    return {
        'name': fish.name,
        'cost': fish.cost,
        'description': fish.description,
        'url': fish.url,
        'weight': fish.weight,
        'components': fish.components
    }