from hashlib import new
from random import choices, randint
from socket import timeout
from discord.ext.commands import Cog, command, has_permissions, guild_only
from discord import Embed
from discord.colour import Colour
from math import ceil
from discord.ext.commands.cooldowns import BucketType

from discord.ext.commands.core import max_concurrency

from handlers import MailHandler
from logging import config, getLogger

from cogs.user_stats import transaction
from database import db
from main import on_command
from models.business import BUSINESSES
from models.paginator import Paginator
from models.errors import CommandCanceled
from models.fishing import *
from models.fishing import components as fish_components
from models.shop import shop_id
from models.business import B
from discord_components import DiscordComponents, component


config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class Shop(Cog):
    def __init__(self, Bot):
        self.Bot = Bot
        logger.info(f"{__name__} Cog has initialized")

    @command(
        usage="`=shop`",
        help="Магазин вашей гильдии, за добавление товаров отвечает администрация"
    )
    @guild_only()
    async def shop(self, ctx):
        await on_command(self.Bot.get_command('shop'))
        shop = await db.fetch_user(ctx.guild.id, shop_id, items=1)
        shop = shop['items']
        embed = Embed(title='Магазин', color=Colour.dark_theme())
        
        if not shop:
            embed.description = "В магазине вашей гильдии нет товаров, обратитесь к администратору!"
            await ctx.send(embed=embed)
        else:
            l = len(shop)
            
            embeds = [Embed(title='Магазин', color=Colour.dark_theme()) for i in range(ceil(l / 5))]
            values = []
            
            for i in range(l):
                embeds[i // 5].add_field(name = "💸 " + str(shop[i]['cost']) + '$   |  ' + shop[i]['name'], value=shop[i]['description'], inline=False)
                values.append(shop[i]['name'])

            c_id = str(ctx.message.id)
            
            p = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=c_id + "pagi96796", values=values, forse=5, timeout=300)
            response, inter, msg = await p.send()
            if response == "Отменить" or response is None:
                await msg.delete()
                return
            
            
            items = await db.fetch_user(ctx.guild.id, shop_id, items=1)
            items = items['items']
            match = False
            for i in items:
                if i['name'] == response:
                    match = True
                    break
            if match:
                embed = Embed(title=i['name'], color=Colour.dark_theme())
                embed.add_field(name='Цена', value=f"{i['cost']}$", inline=False)
                embed.add_field(name='Описание', value=i['description'], inline=False)
                roles = [ctx.guild.get_role(role) for role in i['roles']]
                if not roles:
                    embed.add_field(name='Роли', value='нет', inline=False)
                else:
                    embed.add_field(name='Роли', value=' '.join([role.mention for role in roles]), inline=False)
                await inter.edit_origin(embed=embed, components=[component.Button(style=component.ButtonStyle.blue, label="Купить", custom_id=c_id + "buy_")])
                interaction = await self.Bot.wait_for("button_click", check = lambda i: i.custom_id == c_id + "buy_" and i.user == ctx.author)

                cost = i['cost']
                    
                user_money = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1, inventory=1)
                inventory = user_money['inventory']
                user_money = user_money['money']
                if user_money >= cost:
                    if i not in inventory:
                        embed = Embed(title=f"Поздравляю с покупкой, {i['name']}! Предмет перемещён в ваш `inventory`", color=Colour.dark_theme())
                        await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {'inventory': i}, '$inc': {'money': -cost}})
                    else:
                        embed = Embed(title=f"У вас уже есть этот товар", color=Colour.dark_theme())
                else:
                    embed = Embed(title=f"Недостатчно средств", color=Colour.dark_theme())

                await interaction.edit_origin(embed=embed, components=[])
                
            else:
                embed = Embed(title='Товар не найден', color=Colour.dark_theme())
                await inter.edit_origin(embed=embed, components=[])


    @command(
        usage="`=fshop`",
        help="Рыболовный магазин вашей гильдии"
    )
    @guild_only()
    async def fshop(self, ctx):
        await on_command(self.Bot.get_command('fshop'))
        c_id = str(ctx.message.id)
        embed = Embed(title='Магазин', color=Colour.dark_theme())
        
        components = [[component.Button(label='Удочки', style=component.ButtonStyle.blue, custom_id=c_id + "rod"),
                       component.Button(label='Водоёмы', style=component.ButtonStyle.blue, custom_id=c_id + "pon")]]
        op = await ctx.send(embed=embed, components=components)
        
        interaction = await self.Bot.wait_for("button_click", check = lambda i: (i.custom_id == c_id + "rod" or i.custom_id == c_id + "pon") and i.user == ctx.author)
        if interaction.custom_id[-1:-4:-1][::-1] == 'rod':
            shop = [rods[r] for r in fishing_shop['rods']]
            chose = "rods"
        else:
            shop = [ponds[p] for p in fishing_shop['ponds']]
            chose = "ponds"
        
        shop = shop[1:]

        await op.delete()

        l = len(shop)
        
        embeds = [Embed(title='Магазин', color=Colour.dark_theme()) for i in range(ceil(l / 5))]
        values = []
        for i in range(l):
            embeds[i // 5].add_field(name = "💸 " + str(shop[i].cost) + '$   |  ' + shop[i].name, value=shop[i].description, inline=False)
            values.append(fishing_shop[chose][i + 1])

        p = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=c_id + "pagi151623423", values=values, forse=5, timeout=300)
        response, inter, msg = await p.send()
        if response == "Отменить" or response is None:
            await msg.delete()
            return
        response = int(response)
  
        if chose == 'rods':
            item = rods[response]
        else:
            item = ponds[response]
            
        
        embed = Embed(title=item.name, color=Colour.dark_theme())
        embed.add_field(name='Цена', value=f"{item.cost}$", inline=False)
        embed.add_field(name='Описание', value=item.description, inline=False)
        if chose == 'rods':
            embed.add_field(name="Модификаторы", value=f"x {item.modifiers['x']} к качеству рыбы\nТочность - {item.modifiers['aim']}", inline=False)
        embed.set_image(url=item.url)
        await inter.edit_origin(embed=embed, components=[component.Button(style=component.ButtonStyle.blue, label="Купить", custom_id=c_id + "buy_2")])
        interaction = await self.Bot.wait_for("button_click", check = lambda i: i.custom_id == c_id + "buy_2" and i.user == ctx.author)

        cost = item.cost
            
        user_money = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1, finventory=1)
        inventory = user_money['finventory']
        user_money = user_money['money']
        if user_money >= cost:
            if response not in inventory['ponds']:
                embed = Embed(title=f"Поздравляю с покупкой, {item.name}!", color=Colour.dark_theme())
                await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {f'finventory.{chose}': response}, '$inc': {'money': -cost}})
            else:
                embed = Embed(title=f"У вас уже есть этот товар", color=Colour.dark_theme())
        else:
            embed = Embed(title=f"Недостатчно средств", color=Colour.dark_theme())

        await interaction.edit_origin(embed=embed, components=[])

    
    
    async def is_cost(self, cost):
        try:
            cost = int(cost)
            return cost >= 0
        except:
            return False
    

    @command(
        usage="`=cage`",
        help="Садок"
    )
    @guild_only()
    async def cage(self, ctx):
        await on_command(self.Bot.get_command('cage'))
        c_id = str(ctx.message.id)
        shop = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1, business=1)
        user_components = {str(i): 0 for i in range(1, 9)}
        user_components.update(shop['finventory']['components'])
        cage = shop['finventory']['cage']
        ides = {
            i: cage[i] for i in range(len(cage))
        }

        l = len(cage)
        if l == 0:
            embed = Embed(title='Магазин', color=Colour.dark_theme())
            embed.description = "Вы ещё не отложили не одной рыбы в садок"
            await ctx.send(embed=embed)
            return
        
        embeds = [Embed(title='Магазин', color=Colour.dark_theme()) for i in range(ceil(l / 5))]
        values = []
        
        for i in range(l):
            embeds[i // 5].add_field(name = "💸 " + str(cage[i]['cost']) + '$   |  ' + cage[i]['name'], value=cage[i]['description'], inline=False)
            values.append(i)
            
        p = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=c_id + "pagi3", values=values, forse=5, timeout=300)
        response, inter, msg = await p.send()
        if response == "Отменить" or response is None:
            await msg.delete()
            return
        response = int(response)
        item = ides[response]
            
        
        embed = Embed(title=item['name'], color=Colour.dark_theme())
        embed.add_field(name='Цена', value=f"{item['cost']}$", inline=False)
        embed.add_field(name='Описание', value=item['description'], inline=False)
        embed.set_image(url=item['url'])
        embed.description = f"\nВес: {item['weight']} кг\n"
        cp = "components"
        embed.description += f"\Компоненты: {', '.join([f'{fish_components[i].name} - {item[cp][i]}' for i in item[cp]])}\n"
        components=[[
            component.Button(style=component.ButtonStyle.green, label="Продать", custom_id=c_id + "sell"),
            component.Button(label="Разобрать", style=component.ButtonStyle.green, custom_id=c_id + "disa"),
            component.Button(label="На рынок", style=component.ButtonStyle.green, custom_id=c_id + "market"),
            component.Button(label="Отменить", style=component.ButtonStyle.green, custom_id=c_id + "r")]]
        
        b = shop['business']
        for i in b:
            buss = BUSINESSES[i]
            if not buss.stock:
                components[0].insert(-1, component.Button(label=buss.action_name, style=component.ButtonStyle.blue, custom_id=c_id + f"business{i}"))
        
        await inter.edit_origin(embed=embed, components=components)
        interaction = await self.Bot.wait_for("button_click", check = lambda i: (i.custom_id == c_id + "sell" or i.custom_id == c_id + "disa" or i.custom_id == c_id + "market" or i.custom_id == c_id + "r" or i.custom_id[:-1] == c_id + "business") and i.user == ctx.author)

        
        new_shop = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1)
        new_cage = new_shop['finventory']['cage']
        if item not in new_cage:
            embed = Embed(title="предмета уже нет в садке", color=Colour.dark_theme())
            await interaction.respond(embed=embed, components=[])
            return
        
        
        if interaction.custom_id == c_id + "sell":
            cost, pretty = await B.sell(b, item['cost'], item['name'])
            embed = Embed(title=f"Улов продан, получено: `{pretty}$`", color=Colour.dark_theme())
            await db.update_user(ctx.guild.id, ctx.author.id, {'$unset': {f'finventory.cage.{response}': 1}})
            await db.update_user(ctx.guild.id, ctx.author.id, {'$pull': {f'finventory.cage': None}, '$inc': {'money': cost}})
        elif interaction.custom_id == c_id + "market":
            embed = Embed(title="Введите желаемую цену", color=Colour.dark_theme())
            await interaction.send(embed=embed)
            cost = False
            while not cost:
                message = await self.Bot.wait_for("message", check = lambda m: m.author == ctx.author and m.channel == ctx.channel)
                cost = await self.is_cost(message.content)
                if not cost:
                    await message.reply(embed=Embed(title="Некорректная цена"))
                else:
                    cost = int(message.content)

            await db.update_user(ctx.guild.id, shop_id, {'$push': {'ah': {
                'name': item['name'],
                'cost': item['cost'],
                'description': item['description'],
                'url': item['url'],
                'weight': item['weight'],
                'components': item['components'],
                'seller': ctx.author.id,
                'sellcost': cost,
                'sellername': message.author.display_name,
                'id': f"{ctx.guild.id}{ctx.channel.id}{ctx.message.id}"
            }}})
            await db.update_user(ctx.guild.id, ctx.author.id, {'$unset': {f'finventory.cage.{response}': 1}})
            await db.update_user(ctx.guild.id, ctx.author.id, {'$pull': {f'finventory.cage': None}})
            embed = Embed(title="Товар выставлен на рынок", color=Colour.dark_theme())
            await message.reply(embed=embed)
        elif interaction.custom_id == c_id + "r":
            pass
        elif interaction.custom_id[:-1] == c_id + "business":
            await db.update_user(ctx.guild.id, ctx.author.id, {'$unset': {f'finventory.cage.{response}': 1}})
            await db.update_user(ctx.guild.id, ctx.author.id, {'$pull': {f'finventory.cage': None}})
            b = BUSINESSES[int(interaction.custom_id[-1])]
            e, state = await B.logic(b, ctx.guild.id, ctx.author.id, item['components'], item['cost'], user_components)
            embed=e
        else:
            await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {f'finventory.components.{i}': item['components'][i] for i in item['components']}, '$unset': {f'finventory.cage.{response}': 1}})
            await db.update_user(ctx.guild.id, ctx.author.id, {'$pull': {f'finventory.cage': None}})
            embed = Embed(title=f"Рыба разобрана, получено: {', '.join([f'{fish_components[i].name} - {item[cp][i]}' for i in item[cp]])}", color=Colour.dark_theme())

        await interaction.edit_origin(embed=embed, components=[])



    @command(
        usage="`=workshop`",
        help="Мастерская вашей гильдии"
    )
    @guild_only()
    async def workshop(self, ctx):
        await on_command(self.Bot.get_command('workshop'))
        c_id = str(ctx.message.id)
        embed = Embed(title='Мастерская', color=Colour.dark_theme())
        
        custom_shop = [custom_rods[i] for i in custom_rods]
        l = len(custom_shop)
        custom_shop.extend([boxes[i] for i in boxes])
        
        fcomponents = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1)
        fcomponents = fcomponents['finventory']['components']
        
        le = len(boxes)
        materials = "Инвентарь:\n"
        pr = ", ".join([f'{fish_components[i].re} - {fcomponents[i]}' for i in fcomponents])
        materials += pr if pr != "" else "Пусто"
        embeds = [Embed(title='Мастерская', color=Colour.dark_theme()) for i in range(ceil((l + le) / 5))]
        values = []
        for i in range(l):
            embeds[i // 5].add_field(name=custom_shop[i].name + '  |  ' + ", ".join([f'{i[0].re} - {i[1]}' for i in custom_shop[i].cost]), value=custom_shop[i].description, inline=False)
            embeds[i // 5].description = materials
            values.append(i + 1000)

        for i in range(l, l + le):
            embeds[i // 5].add_field(name=custom_shop[i].name + '  |  ' + ", ".join([f'{i[0].re} - {i[1]}' for i in custom_shop[i].cost]), value=custom_shop[i].description, inline=False)
            embeds[i // 5].description = materials
            values.append(10000 + i - l)
        
        p = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=c_id + "pagi67", values=values, forse=5, timeout=300)
        response, inter, msg = await p.send()
        if response == "Отменить" or response is None:
            await msg.delete()
            return
        response = int(response)
  
        rod = wshop[response]
        
        embed = Embed(title=rod.name, color=Colour.dark_theme())
        embed.description = "Инвентарь:\n" + ", ".join([f'{fish_components[i].name} - {fcomponents[i]}' for i in fcomponents])
        embed.add_field(name='Необходимые материалы', value=", ".join([f'{i[0].name} - {i[1]}' for i in rod.cost]), inline=False)
        embed.add_field(name='Описание', value=rod.description, inline=False)
        if response < 10000:
            embed.add_field(name="Модификаторы", value=f"x {rod.modifiers['x']} к качеству рыбы\nТочность - {rod.modifiers['aim']}", inline=False)
        embed.set_image(url=rod.url)
        await inter.edit_origin(embed=embed, components=[component.Button(style=component.ButtonStyle.blue, label="Собрать", custom_id=c_id + "buy_3")])
        interaction = await self.Bot.wait_for("button_click", check = lambda i: i.custom_id == c_id + "buy_3" and i.user == ctx.author)

        finventory = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1)
        finventory = finventory['finventory']
        user_components = finventory['components']
        
        can_pay = True
        
        for comp, col in rod.cost:
            try:
                if user_components[comp.id] < col:
                    can_pay = False
                    break
            except KeyError:
                can_pay = False
                break
        
        if can_pay:
            if response not in finventory['rods'] and response < 10000:
                embed = Embed(title=f"{rod.name} собран!", color=Colour.dark_theme())
                await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {f'finventory.rods': response}, '$inc': {f'finventory.components.{i[0].id}': -i[1] for i in rod.cost}})
            else:
                if response >= 10000:
                    embed = Embed(title=f"{rod.name} собран!", color=Colour.dark_theme())
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {f'inventory': {
                        'name': rod.name,
                        'cost': rod.cost,
                        'description': rod.description,
                        'loot': rod.loot,
                        'url': rod.url,
                        'tier': rod.tier
                        }}, '$inc': {f'finventory.components.{i[0].id}': -i[1] for i in rod.cost}})
                else:
                    embed = Embed(title=f"У вас уже есть этот товар", color=Colour.dark_theme())
        else:
            embed = Embed(title=f"Недостатчно материалов", color=Colour.dark_theme())

        await interaction.edit_origin(embed=embed, components=[])

    @command(
        usage="`=add_item`",
        help='Добавление товара в магазин гильдии. Активируйте команду и следуйте инструкциям в генераторе товара',
        brief='administrator'
    )
    @guild_only()
    @max_concurrency(1, BucketType.channel, wait=False)
    @has_permissions(administrator=True)
    async def add_item(self, ctx):
        await on_command(self.Bot.get_command('add_item'))
        item_opts = {}
        embed = Embed(
            title='Создание товара',
            color = Colour.dark_theme()
        )
        embed.set_footer(text='Введите название товара | `отменить` для отмены')
        main = await ctx.send(embed=embed)

        def check(m):
            return m.content and m.author.id == ctx.author.id and ctx.guild.id == m.guild.id

        async def get(item_opts, key, place):
            try:
                message = await self.Bot.wait_for('message', check=check, timeout=60)
            except TimeoutError:
                raise CommandCanceled('Команда сброшена')
            else:
                if message.content == 'отменить':
                    raise CommandCanceled('Команда сброшена')
                else:
                    if place == 'content':
                        item_opts[key] = message.content
                    else:
                        item_opts[key] = message.role_mentions
                    return item_opts
        
        
        
        name = False
        
        while name is False:
            item_opts = await get(item_opts, 'name', 'content')
            items = await db.fetch_user(ctx.guild.id, shop_id, items=1)
            items = items['items']
            unicle = True
            for i in items:
                if i['name'] == item_opts['name']:
                    unicle = False
                    embed.set_footer(text='Имя должно быть уникальным | `отменить` для отмены')
            if unicle:
                embed.title = item_opts['name']
                embed.set_footer(text='Введите цену товара | `отменить` для отмены')
                name = True
            await main.edit(embed=embed)
                
        
        cost = False
        while cost is False:
            item_opts = await get(item_opts, 'cost', 'content')
            try:
                item_opts['cost'] = int(item_opts['cost'])
            except ValueError:
                embed.set_footer(text='Введите цену товара [число >= 0] | `отменить` для отмены')
                await main.edit(embed=embed)
            else:
                if item_opts['cost'] < 0:
                    embed.set_footer(text='Введите цену товара [число >= 0] | `отменить` для отмены')
                    await main.edit(embed=embed)
                else:
                    cost = True
        
        embed.add_field(name='Цена', value=item_opts['cost'], inline=False)
        embed.set_footer(text='Введите описание товара | `отменить` для отмены')
        await main.edit(embed=embed)
        
        item_opts = await get(item_opts, 'description', 'content')
        embed.add_field(name='Описание', value=item_opts['description'], inline=False)
        embed.set_footer(text='Введите роль, выдаваемую при покупке | без @role - без роли | `отменить` для отмены')
        await main.edit(embed=embed)
        
        item_opts = await get(item_opts, 'roles', 'roles')
        if item_opts['roles']:
            embed.add_field(name='Роли', value=' '.join([role.mention for role in item_opts['roles']]), inline=False)
        else:
            embed.add_field(name='Роли', value='Нет', inline=False)
        embed.set_footer(text='Товар создан!')
        await main.edit(embed=embed)
        
        n = []
        
        for role in item_opts['roles']:
            n.append(role.id)
        
        item_opts['roles'] = n
        
        await db.update_user(ctx.guild.id, shop_id, {'$push': {'items': item_opts}})
    

    @command(
        usage="`=remove_item [название предмета]`",
        help="Удаление предмета из магазина гильдии",
        brief='administrator'
    )
    @guild_only()
    @has_permissions(administrator=True)
    async def remove_item(self, ctx, *, name):
        await on_command(self.Bot.get_command('remove_item'))
        if not name:
            embed = Embed(title='Товар не найден', color=Colour.dark_theme())
        else:
            items = await db.fetch_user(ctx.guild.id, shop_id, items=1)
            items = items['items']
            match = False
            for i in items:
                if i['name'] == name:
                    match = True
                    break
            if match:
                embed = Embed(title='Товар удалён', color=Colour.dark_theme())
                await db.update_user(ctx.guild.id, shop_id, {'$pull': {'items': {'name': name}}})
            else:
                embed = Embed(title='Товар не найден', color=Colour.dark_theme())
        await ctx.send(embed=embed)



    @command(
        usage="`=reset [exp | money | messages | games | user | shop]`",
        help="Сброс отдельных данных гильдии (exp | money | messages | games), магазина (shop), или всех данных пользователей (user)",
        brief='administrator'
    )
    @guild_only()
    @has_permissions(administrator=True)
    async def reset(self, ctx, *, object):
        await on_command(self.Bot.get_command('reset'))
        embed = Embed(color=Colour.dark_theme())
        if object == 'shop':
            await db.delete_user(ctx.guild.id, shop_id)
            await db.create_shop(ctx.guild.id)
            embed.title = 'Магазин обнулён'
        elif object == 'exp':
            await db.update_guild(ctx.guild.id, {'_id': {'$ne': shop_id}}, {'$set': {'exp': 0, 'level': 1}})
            embed.title = 'уровни пользователей обнулены'
        elif object == 'money':
            await db.update_guild(ctx.guild.id, {'_id': {'$ne': shop_id}},  {'$set': {'money': 1000}})
            embed.title = 'деньги пользователей обнулены'
        elif object == 'messages':
            await db.update_guild(ctx.guild.id, {'_id': {'$ne': shop_id}}, {'$set': {'messages': 0}})
            embed.title = 'сообщения пользователей обнулены'
        elif object == 'games':
            await db.update_guild(ctx.guild.id, {'_id': {'$ne': shop_id}}, {'$set': {'games': 0}})
            embed.title = 'игры пользователей обнулены'
        elif object == 'user':
            await db.update_guild(ctx.guild.id, {'_id': {'$ne': shop_id}}, {'$set': {'exp': 0, 'level': 1, 'money': 1000, 'messages': 0, 'games': 0}})
            embed.title = 'данные пользователей обнулены'
        
        else:
            embed.title = 'Некорректный параметр'
        
        await ctx.send(embed=embed)
    
    
    @command(
        usage="`=inventory`",
        help="Ваш инвентарь, здесь вы можете продать или использовать свои предметы"
    )
    @guild_only()
    async def inventory(self, ctx):
        await on_command(self.Bot.get_command('inventory'))
        items = await db.fetch_user(ctx.guild.id, ctx.author.id, inventory=1)
        items = items['inventory']
        embed = Embed(color=Colour.dark_theme())
        if not items:
            embed.title = "В вашем инвентаре нет товаров"
            await ctx.reply(embed=embed)
        else:
            l = len(items)
            
            embeds = [Embed(title='Инвентарь', color=Colour.dark_theme()) for i in range(ceil(l / 5))]
            values = []

            for i in range(l):
                embeds[i // 5].add_field(name=items[i]['name'], value=items[i]['description'], inline=False)
                values.append(i)
            c_id = str(ctx.message.id)

            p = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=c_id + "pagi908", values=values, forse=5, timeout=300)
            response, inter, msg = await p.send()
            if response == "Отменить" or response is None:
                await msg.delete()
                return

            response = int(response)
            i = items[response]
            embed = Embed(title=i['name'], color=Colour.dark_theme())
            embed.add_field(name='Описание', value=i['description'], inline=False)
            components = [[]]
            b = i.get('loot', False)
            if not b:
                embed.add_field(name='Цена', value=f"{i['cost']}$", inline=False)
                roles = [ctx.guild.get_role(role) for role in i['roles']]
                if not roles:
                    embed.add_field(name='Роли', value='нет', inline=False)
                else:
                    embed.add_field(name='Роли', value=' '.join([role.mention for role in roles]), inline=False)
                    components[0].append(component.Button(style=component.ButtonStyle.blue, label="Использовать", custom_id=c_id + "use5"))
                components[0].append(component.Button(style=component.ButtonStyle.blue, label="Продать", custom_id=c_id + "sel5"))
                await inter.edit_origin(embed=embed, components=components)
            else:
                embed.set_image(url=i['url'])
                components[0].append(component.Button(style=component.ButtonStyle.blue, label="Использовать", custom_id=c_id + "use5"))
                await inter.edit_origin(embed=embed, components=components)
            interaction = await self.Bot.wait_for("button_click", check = lambda i: i.user == ctx.author and (i.custom_id == c_id + "use5" or i.custom_id == c_id + "sel5"))
            
            
            new_items = await db.fetch_user(ctx.guild.id, ctx.author.id, inventory=1)
            new_items = new_items['inventory']
            if i not in new_items:
                embed = Embed(title="предмета уже нет в инвентаре", color=Colour.dark_theme())
                await interaction.respond(embed=embed, components=[])
                return
            
            embed = Embed(color=Colour.dark_theme())
            
            if interaction.custom_id == c_id + 'sel5':
                cost = ceil(i['cost'] * 0.5)
                embed.title = f"Товар продан за {cost}$"
                await db.update_user(ctx.guild.id, ctx.author.id, {'$pull': {'inventory': {'name': i['name']}}, '$inc': {'money': cost}})
            else:
                if not b:
                    if not i['roles']:
                        embed.title = "Товар нельзя использовать"
                    else:
                        roles = [ctx.guild.get_role(role) for role in i['roles']]
                        try:
                            await ctx.author.add_roles(*roles)
                        except Exception as E:
                            embed.title = "Роль была удалена, или находится выше возможностей бота, сообщите администрации"
                            embed.description = "Чтобы бот мог выдать роль, она должна находиться ниже в списке ролей сервера, чем роль бота"
                        else:
                            embed.title = "Товар использован"
                            await db.update_user(ctx.guild.id, ctx.author.id, {'$pull': {'inventory': {'name': i['name']}}})
                else:
                    embed = Embed(title=i['name'])
                    f = i['loot']
                    loot = choices([i[0] for i in f], [i[1] for i in f])
                    loot = prises[loot[0]]
                    if isinstance(loot, tuple):
                        loot = loot[0](loot[1])
                        print(loot)
                    if isinstance(loot, int):
                        embed.description = f"Начислено: `{loot}$`"
                        await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': loot}, '$unset': {f'inventory.{response}': 1}})
                    elif isinstance(loot, str):
                        loot = await get_fish(int(loot), 1, 17, "🌧️ Дождь")
                        embed.description = f"Начислено: `{loot.name}`"
                        await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {'finventory.cage': await json_fish(loot)}, '$unset': {f'inventory.{response}': 1}})
                    else:
                        amount = randint(1 * i['tier'], 5 * i['tier'])
                        await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {f'finventory.components.{loot.id}': amount}, '$unset': {f'inventory.{response}': 1}})
                        embed.description = f"Начислено: `{loot.name}: {amount}`"
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$pull': {f'inventory': None}})
            await interaction.edit_origin(embed=embed, components=[])
                
    @command(
        usage="`=market`",
        help="Рынок гольдии, выставить на продажу: =cage =rods , вернуть предмет - купить (деньги не снимутся)"
    )
    @guild_only()
    async def market(self, ctx):
        await on_command(self.Bot.get_command('market'))
        c_id = str(ctx.message.id)
        
        
        embed = Embed(title='Рынок', color=Colour.dark_theme())
        
        components = [[component.Button(label='Рыба', style=component.ButtonStyle.blue, custom_id=c_id + "ffishs"),
                       component.Button(label='Удочки', style=component.ButtonStyle.blue, custom_id=c_id + "rrodss")]]
        op = await ctx.send(embed=embed, components=components)
        
        interaction = await self.Bot.wait_for("button_click", check = lambda i: (i.custom_id == c_id + "ffishs" or i.custom_id == c_id + "rrodss") and i.user == ctx.author)
        if interaction.custom_id == c_id + "ffishs":
            shop = await db.fetch_user(ctx.guild.id, shop_id, ah=1)
            shop = shop['ah']
            chose = "ah"
        else:
            shop = await db.fetch_user(ctx.guild.id, shop_id, rods=1)
            shop = shop['rods']
            chose = "rods"

        await op.delete()
        
        
        
        l = len(shop)
        
        if l == 0:
            embed.description = "Товаров нет в наличии, для выставления на продажу, используйте =cage и =rods"
            await interaction.send(embed=embed, components=[])
            return
        
        embeds = [Embed(title='Рынок', color=Colour.dark_theme()) for i in range(ceil(l / 5))]
        values = []
        
        if chose == "ah":
            for i in range(l):
                embeds[i // 5].add_field(name=shop[i]['sellername'] + '  |  ' + shop[i]['name'] + ' | ' + str(shop[i]['sellcost']) + " 💸", value="`" + str(shop[i]['cost']) + '$`  |  ' + ', '.join([f"{fish_components[comp].re} : `{shop[i]['components'][comp]}`" for comp in shop[i]['components']]), inline=False)
                values.append(shop[i]['id'])
        else:
            for i in range(l):
                embeds[i // 5].add_field(name=shop[i]['sellername'] + '  |  ' + shop[i]['name'], value=str(shop[i]['sellcost']) + " 💸", inline=False)
                values.append(shop[i]['id'])

        c_id = str(ctx.message.id)
        
        p = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=c_id + "pagi110", values=values, forse=5, timeout=300)
        response, inter, msg = await p.send()
        if response == "Отменить" or response is None:
            await msg.delete()
            return

        for i in shop:
            if i['id'] == response:
                item = i
                break
        
            
        
        embed = Embed(title=item['sellername'] + '  |  ' + item['name'], color=Colour.dark_theme())
        embed.add_field(name='Цена продавца', value=f"`{item['sellcost']}$`", inline=False)
        if chose == 'ah':
            embed.add_field(name='Цена', value=f"`{item['cost']}$`", inline=False)
            embed.description = f"\nВес: {item['weight']} кг\n"
            cp = "components"
            embed.description += f"\Можно разобрать: {', '.join([f'{fish_components[i].name} - {item[cp][i]}' for i in item[cp]])}\n"
        embed.add_field(name='Описание', value=item['description'], inline=False)
        embed.set_image(url=item['url'])
        await inter.edit_origin(embed=embed, components=[[component.Button(style=component.ButtonStyle.green, label="Купить", custom_id=c_id + "bbuy2")]])
        interaction = await self.Bot.wait_for("button_click", check = lambda i: i.custom_id == c_id + "bbuy2" and i.user == ctx.author)

        if ctx.author.id == item['seller']:
            q = await db.db[str(ctx.guild.id)].find_one_and_update({'_id': shop_id}, {'$pull': {chose: {'id': item['id']}}})
            exists = False
            for i in q[chose]:
                if i['id'] == item['id']:
                    exists = True
                    break
            if exists:
                if chose == 'ah':
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {'finventory.cage': {
                    'name': item['name'],
                    'cost': item['cost'],
                    'description': item['description'],
                    'url': item['url'],
                    'weight': item['weight'],
                    'components': item['components']
                }}})
                else:
                    r_index = 0
                    for i in all_rods:
                        if all_rods[i].name == item['name']:
                            r_index = i
                            break
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {'finventory.rods': r_index}})
                embed = Embed(title="Вы вернули свой товар", color=Colour.dark_theme())
            else:
                embed = Embed(title="Кто-то уже купил ваш товар", color=Colour.dark_theme())
        else:
            user_money = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1)
            user_money = user_money['money']
            if user_money >= item['sellcost']:
                q = await db.db[str(ctx.guild.id)].find_one_and_update({'_id': shop_id}, {'$pull': {chose: {'id': item['id']}}})
                exists = False
                for i in q[chose]:
                    if i['id'] == item['id']:
                        exists = True
                        break
                if exists:
                    if chose == 'ah':
                        await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {'finventory.cage': {
                        'name': item['name'],
                        'cost': item['cost'],
                        'description': item['description'],
                        'url': item['url'],
                        'weight': item['weight'],
                        'components': item['components']
                    }}})
                    else:
                        r_index = 0
                        for i in all_rods:
                            if all_rods[i].name == item['name']:
                                r_index = i
                                break
                        await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {'finventory.rods': r_index}})
                    
                    await transaction((ctx.guild.id, ctx.author.id), (ctx.guild.id, item['seller']), item['sellcost'])
                    embed = Embed(title=f"Поздравляю с покупкой, {item['name']}!", color=Colour.dark_theme())
                    seller = ctx.guild.get_member(item['seller'])
                    e = Embed(title="Ваш товар был продан", color=Colour.dark_theme())
                    e.add_field(name=item['sellername'] + '  |  ' + item['name'] + ' | ' + str(item['sellcost']) + " 💸", value="`" + str(item['cost']) + '$`  |  ' + ', '.join([f"{fish_components[comp].re} : `{item['components'][comp]}`" for comp in item['components']]), inline=False)
                    await seller.send(embed=e)
                else:
                    embed = Embed(title=f"Кто-то оказался быстрее", color=Colour.dark_theme())
            else:
                embed = Embed(title=f"Недостатчно средств", color=Colour.dark_theme())

        await interaction.edit_origin(embed=embed, components=[])


    @command(
        usage="`=rods`",
        help="Коллекция удочек"
    )
    @guild_only()
    async def rods(self, ctx):
        await on_command(self.Bot.get_command('rods'))
        c_id = str(ctx.message.id)
        shop = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1)
        rods = shop['finventory']['rods']
        
        l = len(rods)
        
        embeds = [Embed(title='Ваша коллекция удочек', color=Colour.dark_theme()) for i in range(ceil(l / 5))]
        values = []
        
        for i in range(l):
            rod = all_rods[rods[i]]
            embeds[i // 5].add_field(name = rod.name, value=rod.description, inline=False)
            values.append(i)
            
        p = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=c_id + "pagi68", values=values, forse=5, timeout=300)
        response, inter, msg = await p.send()
        if response == "Отменить" or response is None:
            await msg.delete()
            return
        response = int(response)
        item = all_rods[rods[response]]
            
        
        embed = Embed(title=item.name, color=Colour.dark_theme())
        embed.add_field(name='Описание', value=item.description, inline=False)
        embed.set_image(url=item.url)
        if item.name != "Бамбук":
            await inter.edit_origin(embed=embed, components=[[component.Button(label="На рынок", style=component.ButtonStyle.green, custom_id=c_id + "market2"), component.Button(label="Отменить", style=component.ButtonStyle.green, custom_id=c_id + "r2")]])
            interaction = await self.Bot.wait_for("button_click", check = lambda i: (i.custom_id == c_id + "market2" or i.custom_id == c_id + "r2") and i.user == ctx.author)
            if interaction.custom_id == c_id + "market2":
                embed = Embed(title="Введите желаемую цену", color=Colour.dark_theme())
                await interaction.send(embed=embed)
                cost = False
                while not cost:
                    message = await self.Bot.wait_for("message", check = lambda m: m.author == ctx.author and m.channel == ctx.channel)
                    cost = await self.is_cost(message.content)
                    if not cost:
                        await message.reply(embed=Embed(title="Некорректная цена"))
                    else:
                        cost = int(message.content)
                
                
                embed = Embed(title="Обрабатываем...", color=Colour.dark_theme())
                r = await interaction.send(embed=embed, components=[])
                
                new_shop = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1)
                new_rods = new_shop['finventory']['rods']
                print(item.id, new_rods)
                if item.id not in new_rods:
                    embed = Embed(title="удочка уже не у вас", color=Colour.dark_theme())
                    await message.reply(embed=embed)
                    return
                
                await db.update_user(ctx.guild.id, shop_id, {'$push': {'rods': {
                    'name': item.name,
                    'cost': item.cost,
                    'description': item.description,
                    'url': item.url,
                    'seller': ctx.author.id,
                    'sellcost': cost,
                    'sellername': message.author.display_name,
                    'id': f"{ctx.guild.id}{ctx.channel.id}{ctx.message.id}"
                }}})
                await db.update_user(ctx.guild.id, ctx.author.id, {'$unset': {f'finventory.rods.{response}': 1}})
                await db.update_user(ctx.guild.id, ctx.author.id, {'$pull': {f'finventory.rods': None}})
                embed = Embed(title="Товар выставлен на рынок", color=Colour.dark_theme())
                await message.reply(embed=embed)
            else:
                await interaction.edit_origin(embed=embed, components=[])
        else:
            await inter.edit_origin(embed=embed, components=[])
    
    @command()
    @guild_only()
    async def business(self, ctx):
        await on_command(self.Bot.get_command('business'))
        c_id = str(ctx.message.id)
        embed = Embed(title='Бизнесы', color=Colour.dark_theme())
        
        buss = [BUSINESSES[i] for i in BUSINESSES]
        l = len(buss)
        
        fcomponents = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1, business=1)
        fbusiness = fcomponents['business']
        fcomponents = fcomponents['finventory']['components']
        
        materials = "Инвентарь:\n"
        pr = ", ".join([f'{fish_components[i].re} - {fcomponents[i]}' for i in fcomponents])
        materials += pr if pr != "" else "Пусто"
        embeds = [Embed(title='Бизнесы', color=Colour.dark_theme()) for i in range(ceil(l / 5))]
        values = []
        for i in range(l):
            embeds[i // 5].add_field(name=buss[i].name + '  |  ' + ", ".join([f'{i[0].re}-{i[1]}' for i in buss[i].cost]), value=buss[i].description, inline=False)
            embeds[i // 5].description = materials
            values.append(i)
        
        p = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=c_id + "pagi148856", values=values, forse=5, timeout=300)
        response, inter, msg = await p.send()
        if response == "Отменить" or response is None:
            await msg.delete()
            return
        response = int(response)
  
        b = buss[response]
        
        embed = Embed(title=b.name, color=Colour.dark_theme())
        embed.description = "Инвентарь:\n" + ", ".join([f'{fish_components[i].name} - {fcomponents[i]}' for i in fcomponents])
        embed.add_field(name='Необходимые материалы', value=", ".join([f'{i[0].name} - {i[1]}' for i in b.cost]), inline=False)
        embed.add_field(name='Описание', value=b.description, inline=False)
        await inter.edit_origin(embed=embed, components=[component.Button(style=component.ButtonStyle.blue, label="Собрать", custom_id=c_id + "buy_991")])
        interaction = await self.Bot.wait_for("button_click", check = lambda i: i.custom_id == c_id + "buy_991" and i.user == ctx.author)

        finventory = await db.fetch_user(ctx.guild.id, ctx.author.id, finventory=1)
        finventory = finventory['finventory']
        user_components = finventory['components']
        
        can_pay = True
        
        for comp, col in b.cost:
            try:
                if user_components[comp.id] < col:
                    can_pay = False
                    break
            except KeyError:
                can_pay = False
                break
        
        if can_pay:
            if response not in fbusiness:
                embed = Embed(title=f"{b.name} куплен!", color=Colour.dark_theme())
                await db.update_user(ctx.guild.id, ctx.author.id, {'$push': {f'business': response}, '$inc': {f'finventory.components.{i[0].id}': -i[1] for i in b.cost}})
            else:
                embed = Embed(title=f"У вас уже есть этот бизнес", color=Colour.dark_theme())
        else:
            embed = Embed(title=f"Недостатчно материалов", color=Colour.dark_theme())

        await interaction.edit_origin(embed=embed, components=[])



def setup(Bot):
    Bot.add_cog(Shop(Bot))
