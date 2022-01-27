from asyncio.tasks import sleep
from collections import namedtuple
from time import time
from discord.ext.commands import Cog, command, guild_only
from discord import Embed, Colour
from asyncio import TimeoutError
from random import randint, choices, random, shuffle
from cogs.leveling import LevelTable

from database import db
from math import sqrt
from discord_components.component import Select, SelectOption, Button, ButtonStyle

from main import on_command
from models.fishing import *
from models.fishing import components as fish_components
from models.business import BUSINESSES, B, SUCCESS

fish = namedtuple('fish', ['url', 'cost', 'chance', 'name'])
fishes = [
    fish("https://key0.cc/images/preview/111781_c674df9fa58a5ad9cc1c1d9394a5d6bc.png", 10, 0.5, 'Кислотная рыба'),
    fish("https://key0.cc/images/preview/97955_e25d2bd07b16fc7e870e6d3421901d02.png", 0, 0.5, 'Кости')
]

class Jobs(Cog):

    __waitingFish = lambda self: randint(1, 30)
    modifier = lambda self, level: sqrt(level)

    def __init__(self, Bot):
        self.Bot = Bot
        self.games = {} #{message.id: [bool, author]}
        temperature = randint(0, 30), randint(0, 30)
        self.max_temp = max(temperature)
        self.min_temp = min(temperature)
        self.temperature = self.gen_temp()
        self.fortune_number = randint(2, 12)
        self.weather = self.gen_weather()
        

    def gen_temp(self):
        temperature = {}
        for t in range(0, 24):
            if t in range(3, 15 + 1):
                temperature[t] = round(self.min_temp + (self.max_temp - self.min_temp) / 12 * (t - 3))
            else:
                if t in range(0, 3):
                    t += 24
                temperature[t] = round(self.max_temp - (self.max_temp - self.min_temp) / 12 * abs(t - 15))

        return temperature

    def gen_weather(self):
        weather = {}
        for t in range(0, 24):
            mod = t % self.fortune_number
            if mod == 0:
                weather[t] = "🌧️ Дождь"
            elif mod == 1:
                weather[t] = "🌫️ Туман"
            else:
                weather[t] = "🌞 Ясно"
        return weather
            

    @command(
        usage="`=fish`",
        help="Рыбалка. для справки - `=guide`"
    )
    @guild_only()
    async def fish(self, ctx):
        await on_command(self.Bot.get_command('fish'))
        embed = Embed(
            title="Рыбалка",
            color=Colour.dark_theme()
        )
        
        finventory = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1, business=1)
        business = finventory['business']
        finventory = finventory['finventory']
        p = [ponds[i] for i in finventory['ponds']]
        r = [all_rods[i] for i in set(finventory['rods'])]
        
        t = time() // 3600 % 24
        temp = self.temperature[t]
        weather = self.weather[t]
        footer = f"🌡 Температура: {temp} ℃ | Погода: {weather}"
        embed.set_footer(text=footer, icon_url=self.Bot.user.avatar_url)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        c_id = str(ctx.message.id)
        components = [Select(
            placeholder="Удилище",
            options=[SelectOption(label=item.name, value=item.id) for item in r],
            custom_id=c_id + "rod"
        ),
                      Select(
            placeholder="Водоём",
            options=[SelectOption(label=item.name, value=item.id) for item in p],
            custom_id=c_id + "pon"
        )]
        main = await ctx.send(embed=embed, components=components)
        o = 0
        while o < 2:
            interaction = await self.Bot.wait_for('select_option')
            if (interaction.custom_id == c_id + "rod" or interaction.custom_id == c_id + "pon") and interaction.user == ctx.author:
                o += 1
                response = int(interaction.values[0])
                if interaction.custom_id[-1:-4:-1][::-1] == 'rod':
                    item = all_rods[response]
                    embed.set_thumbnail(url=item.url)
                    embed.add_field(name="Удилище", value=item.name)
                    main_rod = item
                else:
                    item = ponds[response]
                    embed.set_image(url=item.url)
                    embed.add_field(name="Водоём", value=item.name)
                    main_pond = item
                if len(components) == 2:
                    components.pop(0 if interaction.custom_id[-1:-4:-1][::-1] == 'rod' else 1)
                else:
                    components = [Button(label="Рыбачить", style=ButtonStyle.green, custom_id=c_id + "fish")]
                await interaction.edit_origin(embed=embed, components=components)
        user_data = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1, finventory=1)
        user_components = {str(i): 0 for i in range(1, 9)}
        user_components.update(user_data['finventory']['components'])
        catched = 0
        
        start = time()
        while time() - start < 300:
            try:
                interaction = await self.Bot.wait_for("button_click", check = lambda i: i.custom_id == c_id + "fish" and i.user == ctx.author, timeout=60)
            except TimeoutError:
                start = time()
            else:
                e = Embed(title=f"Погода: {footer}", color=Colour.dark_theme())
                e.description = f"Поймано за заход: `{catched}`   | Инвентарь:\n"
                pl = ', '.join([f'{fish_components[i].re} - `{user_components[i]}`' for i in user_components if user_components[i] != 0])
                e.description += pl if pl != "" else "Пусто"
                await interaction.respond(embed=e)
                screen = (44, 12)
                aspect = screen[0] / screen[1]
                x_y = 11 / 24
                embed = Embed(title="Рыбачим | Нажмите на эмодзи, когда круги совпадут", color=Colour.dark_theme())
                description = ("`" + "." * 44 + "`\n") * 12
                embed.description = description
                r = await ctx.send(embed=embed)
                await r.add_reaction("🎣")
                self.games[r.id] = [False, ctx.author.id]
                co = 0.5
                st = time()
                circle = round(random(), 1)
                if circle > 0.9: circle = 0.9
                timeout = 13
                
                coc = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
                shuffle(coc)
                
                while not self.games[r.id][0]:
                    await sleep(1)
                    if time() - st > timeout or self.games[r.id][0]:
                        #self.games[r.id][0] = True
                        break
                    description = ""
                    co = coc[0]
                    coc.pop(0)
                    for y in range(screen[1]):
                        y_cord = y / screen[1] * 2 - 1
                        for x in range(screen[0]):
                            x_cord = x / screen[0] * 2 - 1
                            x_cord *= aspect * x_y
                            if round(x_cord ** 2 + y_cord ** 2, 1) == co:
                                description += "*"
                            elif round(x_cord ** 2 + y_cord ** 2, 1) == circle:
                                description += "@"
                            else:
                                description += "."
                        description += "\n"
                    embed.description = "```"+description+"```"
                    await r.edit(embed=embed)
                
                catch = abs(co - circle) <= main_rod.modifiers['aim'] * 0.1
                if catch:
                    catched += 1
                    f = main_pond.modifiers['chances']
                    fish = choices([i.id for i in f], [i.chance for i in f])
                    fish_index = fish[0]
                    fish = await get_fish(fish_index, main_rod.modifiers['x'], temp, weather, time=t, t=main_rod.modifiers.get("time", None), w=main_rod.modifiers.get("weather", None))
                    embed = Embed(title=f"Поймана рыба: {fish.name}", color=Colour.dark_theme())
                    embed.set_image(url=fish.url)
                    embed.add_field(name="Стоимость", value=fish.cost)
                    embed.description = fish.description
                    embed.description += f"\nВес: {fish.weight} кг\n"
                    embed.description += f"\Компоненты: {', '.join([f'{fish_components[i].name} - {fish.components[i]}' for i in fish.components])}\n"
                    components = [
                        [Button(label="Продать", style=ButtonStyle.green, custom_id=c_id + "sell"),
                         Button(label="В садок", style=ButtonStyle.green, custom_id=c_id + "cage"),
                         Button(label="Разобрать", style=ButtonStyle.green, custom_id=c_id + "disa")]
                        ]
                    print(business)
                    for i in business:
                        b = BUSINESSES[i]
                        if not b.stock:
                            components[0].append(Button(label=b.action_name, style=ButtonStyle.blue, custom_id=c_id + f"business{i}"))
                        
                    r = await ctx.send(embed=embed, components=components)
                    o = False
                    while not o:
                        try:
                            #!!!warning поддерживает до 9 бизнесов, 10-й работать не будет из-за [:-1]
                            interaction = await self.Bot.wait_for("button_click", check = lambda i: (i.custom_id == c_id + "sell" or i.custom_id == c_id + "cage" or i.custom_id == c_id + "disa" or i.custom_id[:-1] == c_id + "business") and i.user == ctx.author, timeout=60)
                        except TimeoutError:
                            await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {f'finventory.cage': await json_fish(fish)}})
                            await interaction.edit_origin(embed=Embed(title="Улов отправлен в садок", color=Colour.dark_theme()), components=[])
                        else:
                            print(interaction.custom_id)
                            if interaction.custom_id == c_id + "sell":
                                o = True
                                cost, pretty = await B.sell(business, fish.cost, fish.name)
                                await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': cost, 'exp': LevelTable['fishing']}})
                                await interaction.edit_origin(embed=Embed(title=f"Улов продан, получено: `{pretty}$`", color=Colour.dark_theme()), components=[Button(label="Рыбачить", style=ButtonStyle.blue, custom_id=c_id + "fish")])
                            elif interaction.custom_id == c_id + "disa":
                                o = True
                                q = {f'finventory.components.{i}': fish.components[i] for i in fish.components}
                                q['exp'] = LevelTable['fishing']
                                await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': q})
                                for i in fish.components:
                                    user_components[i] += fish.components[i]
                                await interaction.edit_origin(embed=Embed(title=f"Рыба разобрана, получено: {', '.join([f'{fish_components[i].name} - {fish.components[i]}' for i in fish.components])}", color=Colour.dark_theme()), components=[Button(label="Рыбачить", style=ButtonStyle.blue, custom_id=c_id + "fish")])
                            elif interaction.custom_id[:-1] == c_id + "business":
                                b = BUSINESSES[int(interaction.custom_id[-1])]
                                e, state = await B.logic(b, ctx.guild.id, ctx.author.id, fish.components, fish.cost, user_components)
                                if state is SUCCESS:
                                    o = True
                                    await interaction.edit_origin(embed=e, components=[Button(label="Рыбачить", style=ButtonStyle.blue, custom_id=c_id + "fish")])
                                else:
                                    await interaction.send(embed=e)
                            else:
                                o = True
                                await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {'finventory.cage': await json_fish(fish)}, '$inc': {'exp': LevelTable['fishing']}})
                                await interaction.edit_origin(embed=Embed(title="Улов отправлен в садок", color=Colour.dark_theme()), components=[Button(label="Рыбачить", style=ButtonStyle.blue, custom_id=c_id + "fish")])
                else:
                    embed = Embed(title="Рыба ускользнула", color=Colour.dark_theme())
                    components = [Button(label="Рыбачить", style=ButtonStyle.blue, custom_id=c_id + "fish")]
                    await ctx.send(embed=embed, components=components)
                start = time()

        print("finished")
    
    
    @command(
        usage="`=guide`",
        help='Введение в рыболовство'
    )
    async def guide(self, ctx):
        await on_command(self.Bot.get_command('guide'))
        embed = Embed(title="Введение в рыбалку", color=Colour.dark_theme())
        embed.add_field(name="**Общие сведения**", value="Для рыбалки используйте команду `=fish`, выберете удочку | спининг , водоём и нажмите 'рыбачить'", inline=False)
        embed.add_field(name="**Механика ловли**", value="Для поимки рыбы необходимо нажать на эмодзи: 🎣 в момент, когда 2 круга сходятся в 1.\nОт точности удочки зависит разброс между кругами, при котором рыба не ускользнёт. При точности 1: Круг(*) не должен быть дальше Круга (@) на 1 итерацию", inline=False)
        embed.add_field(name="**Где узнать точность?**", value="Точность указана под соответствующей удочкой в рыболовном магазине `=fshop` => удилища. Для Бамбук: 1", inline=False)
        embed.add_field(name="**Нажали ровно в тайминг, но рыба ускользнула?**", value="Присутствует задержка, попробуйте брать на упреждение и у вас обязательно получится.", inline=False)
        embed.add_field(name="**Инвентарь | Компоненты | Мастерская | Магазин**", value="Пойманые рыбы можно разобрать на компоненты:\nБамбук | BA , Карбон | CA , Композит | CO , Керамика | CE , Алюминий | AL , Графит | GR , Нейлон | NY , Капрон | KA\nОни будут видны в рыболовном инвентаре, а также в мастерской `=workshop`\nВ Мастерской можно собрать удочку из компонентов\nВозможно покупать удочки и водоёмы за деньги в рыболовном магазине `=fshop`", inline=False)
        embed.add_field(name="**Как узнать, из какой рыбы выпадает нужный компонент?**", value="Вы потеряли память, но вспоминаете всё, что познаёте", inline=False)
        embed.add_field(name="**Садок**", value="Поймали рекордного сома, но друзья далеко? Не беда! Отложите его в садок!\nВпоследствие сома можно будет продать, или разобрать", inline=False)
        embed.add_field(name="**Качество рыбы**", value="У удочек есть показатель 'x' к качеству рыбы. От него зависит цена рыбы и количество компонентов при разборке\nНа качество также влияет погода. Идеальная погода - 15 ℃ - 20 ℃ и дождь. В ином случае качество будет несколько хуже.", inline=False)
        embed.add_field(name="**Обратите внимание**", value="Некоторые удочки имеют скрытый множитель к качеству рыбы, зависящий от определённых условий. Обнаружить такие удочки можно по её описанию", inline=False)
        embed.add_field(name="**Остались вопросы | предложения ?**", value="`=offer`", inline=False)
        embed.set_author(name="Papr1ka#8145", icon_url="https://cdn.discordapp.com/avatars/397352286487052288/503e1f8c57ea6cdb3fefb8ed6d695059.webp?size=80")
        await ctx.send(embed=embed)
        
    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.__str__() == "🎣" and not payload.member.bot:
            try:
                author = self.games[payload.message_id][1]
                if author == payload.user_id:
                    self.games[payload.message_id][0] = True
            except KeyError:
                pass

def setup(Bot):
    Bot.add_cog(Jobs(Bot))