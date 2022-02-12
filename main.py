from asyncio import sleep
from math import ceil
from pprint import pprint
from discord import Member, Embed, Intents
from discord.colour import Colour
from discord.ext.commands import AutoShardedBot as Robot
from os import environ
from logging import config, getLogger
from discord.ext.commands.core import guild_only, is_owner
from discord.errors import HTTPException
from database import db
from handlers import MailHandler
from discord_components import DiscordComponents, Button, ButtonStyle
from json import loads
from time import time
from models.fishing import wshop
from models.shop import shop_id
#from models.data import Data


config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())
logger.info('starting...')
getLogger('discord').setLevel('WARNING')
getLogger('requests').setLevel('WARNING')
getLogger('urllib3').setLevel('WARNING')
getLogger('aiohttp').setLevel('WARNING')
getLogger('asyncio').setLevel('WARNING')
getLogger('PIL').setLevel('WARNING')

ints = Intents(guilds=True, members=True, guild_messages=True, guild_reactions=True)

Token = environ.get("TOKEN")
Bot = Robot(shard_count=8, command_prefix="=", intents=ints)
DBot = DiscordComponents(Bot)
bad_guilds = []
bot_ides = [883201346759704606, 936355038245302292]
#data = Data()

@Bot.event
async def on_ready():
    logger.info("bot is started")


@Bot.event
async def on_guild_join(guild):
    logger.info(f"bot joined guild: region - {guild.region} | name - {guild.name} | members - {guild.member_count}")
    can_connect = True
    for i in bot_ides:
        if i != Bot.user.id:
            try:
                bot = await guild.fetch_member(i)
            except HTTPException:
                pass
            else:
                can_connect = False
                break
        
    if not can_connect:
        bad_guilds.append(guild.id)
        try:
            e = Embed(title="На сервере не может быть более 1 бота казино", color=Colour.red())
            channel = guild.system_channel
            if not channel is None:
                await channel.send(embed=e)
        except Exception as E:
            logger.warning(E)
        disc = False
        await sleep(5)
        while not disc:
            try:
                await guild.leave()
            except:
                pass
            else:
                disc = True
        
        logger.info(f"bot removed from guild, found casino: region - {guild.region} | name - {guild.name} | members - {guild.member_count}")
    else:
        await db.create_shop(guild.id)

@Bot.event
async def on_guild_remove(guild):
    logger.info(f"bot removed from guild: region - {guild.region} | name - {guild.name} | members - {guild.member_count}")
    if guild.id not in bad_guilds:
        await db.remove_guild(guild.id)
    else:
        bad_guilds.remove(guild.id)

@Bot.event
async def on_member_remove(member: Member):
    await db.delete_user(member.guild.id, member.id)

Bot.remove_command('help')

@Bot.command()
async def help(ctx, module_command=None):
    await on_command(Bot.get_command('help'))
    modules = ('casino', 'user', 'store', 'fishing', 'admin')
    embed = Embed(color=Colour.dark_theme())
    if not module_command:
        embed.title=f"{Bot.user.name} модули"
        embed.add_field(name='Казино', value='`=help casino`', inline=True)
        embed.add_field(name='Пользовательское', value='`=help user`', inline=True)
        embed.add_field(name='Магазин', value='`=help store`', inline=True)
        embed.add_field(name='Рыбалка', value='`=help fishing`', inline=True)
        embed.add_field(name='Настройка', value='`=help admin`', inline=True)
    else:
        if module_command in modules:
            if module_command == 'casino':
                embed.title=f"{Bot.user.name} casino команды"
                embed.add_field(name='Рулетка', value='`=rulet`', inline=False)
                embed.add_field(name='Блэкджек', value='`=blackjack [ставка]`', inline=False)
                embed.add_field(name='Слоты', value='`=slots [ставка]`', inline=False)
                embed.add_field(name='Кости', value='`=dice [ставка] @(оппонент)`', inline=False)
                embed.add_field(name='Камень, Ножницы, Бумага', value='`=rps [ставка] @(оппонент)`', inline=False)
            elif module_command == 'user':
                embed.title=f"{Bot.user.name} user команды"
                embed.add_field(name='Статистика пользователя', value='`=stats`', inline=False)
                embed.add_field(name='Карточка пользователя', value='`=status`', inline=False)
                embed.add_field(name='Сменить тему карточки пользователя', value='`=theme`', inline=False)
                embed.add_field(name='Сменить описание карточки пользователя', value='`=custom [описание]`', inline=False)
                embed.add_field(name='Топ участников по опыту', value='`=scoreboard`', inline=False)
                embed.add_field(name='Топ участников по зажиточности', value='`=godboard`', inline=False)
                embed.add_field(name='Перевести деньги', value='`=pay @[пользователь] [сумма]`', inline=False)
                embed.add_field(name='Предложить идею', value='`=offer [идея]`', inline=False)
                embed.add_field(name='Инвентарь', value='`=inventory`', inline=False)
                embed.add_field(name='Голосовать', value='`=vote`', inline=False)
                embed.add_field(name='Сайт', value='`=url`', inline=False)
            elif module_command == 'store':
                embed.title=f"{Bot.user.name} shop команды"
                embed.add_field(name='Магазин', value='`=shop`', inline=False)
                embed.add_field(name='Рынок', value='`=market`', inline=False)
                embed.add_field(name='Рыболовный магазин', value='`=fshop`', inline=False)
                embed.add_field(name='Рынок', value='`=market`', inline=False)
                embed.add_field(name='Мастерская', value='`=workshop`', inline=False)
                embed.add_field(name='Бизнесы', value='`=business`', inline=False)
            elif module_command == 'fishing':
                embed.title=f"{Bot.user.name} fishing команды"
                embed.add_field(name='Рыбачить', value='`=fish`', inline=False)
                embed.add_field(name='Рыболовный магазин', value='`=fshop`', inline=False)
                embed.add_field(name='Садок', value='`=cage`', inline=False)
                embed.add_field(name='Удочки', value='`=rods`', inline=False)
                embed.add_field(name='Мастерская', value='`=workshop`', inline=False)
                embed.add_field(name='Рынок', value='`=market`', inline=False)
                embed.add_field(name='Гайд по рыбалке', value='`=guide`', inline=False)
                embed.add_field(name='Бизнесы', value='`=business`', inline=False)
            elif module_command == 'admin':
                embed.title=f"{Bot.user.name} admin команды"
                embed.add_field(name='Сбросить данные пользователей', value='`=reset [exp | money | messages | games | user | shop]`', inline=False)
                embed.add_field(name='Добавить товар в магазин', value='`=add_item`', inline=False)
                embed.add_field(name='Удалить товар из магазина', value='`=remove_item`', inline=False)
                embed.add_field(name='Пополнить баланс пользователя', value='`=give @[пользователь] [сумма]`', inline=False)
            else:
                embed.title=f"Модуль не найден"
        else:
            for i in Bot.commands:
                if i.name == module_command:
                    break
            
            if i.name != module_command:
                embed.title = "Команда не найдена"
            else:
                embed.title = i.name
                embed.add_field(name='Использование', value=i.usage, inline=False)
                embed.description = i.help
                if i.brief:
                    embed.add_field(name="Полномочия", value=i.brief)
    
    await ctx.send(embed=embed)


async def on_command(command):
    #await data.on_command()
    logger.info(command)

#Bot.loop.create_task(data.loop())


@Bot.command(
    help="Проголосуйте за бота и получите 3 подарочных коробки! (раз в 12 часов)",
    usage="`=vote`"
)
@guild_only()
async def vote(ctx):
    await on_command(Bot.get_command('vote'))
    status, r = await db.dblget_user_vote(ctx.author.id)
    embed = Embed(title=ctx.author.display_name, color=Colour.dark_purple())
    if status == 200:
        voted = False if not r['voted'] else True
        if voted:
            rod = wshop[10001]
            last_vote = await db.fetch_user(ctx.guild.id, ctx.author.id, claim=1)
            last_vote = last_vote['claim']
            now_time = time()
            if last_vote != 0:
                diff = now_time - last_vote
                if diff >= 43200:
                    embed.title = "**Спасибо за голос! Начислено: `3 подарочных коробки`** Голосуйте снова через 12ч"
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$set': {'claim': now_time},
                                                                   '$push': {f'inventory': {'$each': [{
                        'name': rod.name,
                        'cost': rod.cost,
                        'description': rod.description,
                        'loot': rod.loot,
                        'url': rod.url,
                        'tier': rod.tier
                        } for i in range(3)]}}})
                else:
                    diff = 43200 - diff
                    h = int(diff // 3600)
                    m = ceil((diff - h * 3600) / 60)
                    embed.title = f"**Вы уже получили награду, голосуйте через {h} часов, {m} минут!**"
            else:
                embed.title = "**Спасибо за голос! Начислено: `3 подарочных коробки`** Голосуйте снова через 12ч"
                await db.update_user(ctx.guild.id, ctx.author.id, {'$set': {'claim': now_time},
                                                                   '$push': {f'inventory': {'$each': [{
                        'name': rod.name,
                        'cost': rod.cost,
                        'description': rod.description,
                        'loot': rod.loot,
                        'url': rod.url,
                        'tier': rod.tier
                        } for i in range(3)]}}})
        else:
            embed.title = "**Чтобы получить награду, проголосуйте на сайте и напишите `=vote`**"
            embed.url = 'https://top.gg/bot/883201346759704606/vote'
    elif status == 401:
        logger.error(f"Topgg auth if failed; {r}")
        embed.title = "Обратитесь позже"
    else:
        logger.error(f"Topgg search failed, status:{r.status}; {r}")
        embed.title = "Сервера сайта недоступны, обратитесь позже"
    await ctx.send(embed=embed)


@Bot.command()
@is_owner()
async def announcement(ctx, *, annonce):
    print(annonce)
    send = 0
    annonce = loads(annonce)
    embed = Embed.from_dict(annonce)
    for guild in Bot.guilds:
        try:
            channel = guild.system_channel
            if not channel is None:
                await channel.send(embed=embed)
                send += 1
        except Exception as E:
            logger.warning(E)
    print(send)


@Bot.command()
@is_owner()
async def add(ctx):
    for i in range(100):
        await db.db[f'shard{i}'].create_index('guild_id')
    print('finished')

@Bot.command(
    help="Постоянная ссылка на наш сайт",
    usage="`=url`"
)
async def url(ctx):
    embed = Embed(title="Смотрите команды и следите за новостями на нашем сайте!", color=Colour.dark_theme())
    components = [Button(label='Наш сайт', url='https://casino-web.herokuapp.com/casino/', style=ButtonStyle.URL)]
    await ctx.send(embed=embed, components=components)

"""@Bot.command()
@is_owner()
async def migrate(ctx):
    for i in [453565320708489226]:
        documents = db.db[str(i)].find({})
        docs = await documents.to_list(length=None)
        pprint(docs)
        
        new_docs = []
        
        j = 0
        for document in docs:
            if document['_id'] != -1:
                if document['exp'] == 0 and document['money'] == 1000 and document['level'] == 1 and document['games'] == 0 and document['messages'] == 0 and document['custom'] == "игрок" and document['inventory'] == [] and document['finventory'] == {
        'rods': [1],
        'ponds': [1],
        'cage': [],
        'components': {}
    } and document['business'] == [] and document['claim'] == 0 and document['color'] == 'dark':
                    pass
                else:
                    document['guild_id'] = i
                    new_docs.append(document)
            else:
                document['guild_id'] = i
                document['_id'] = shop_id(i)
                new_docs.append(document)
            j += 1
        shard = await db2.get_shard(i)
        if new_docs:
            await db2.db[shard].insert_many(new_docs)
        print(shard)
    
    
    print('finished')"""



def start():
    logger.info("loading extensions...")
    Bot.load_extension("cogs.casino")
    Bot.load_extension("cogs.error_handler")
    Bot.load_extension("cogs.leveling")
    Bot.load_extension("cogs.user_stats")
    Bot.load_extension("cogs.jobs")
    Bot.load_extension("cogs.shop")
    logger.info("loading complete")
    Bot.run(Token)


if __name__ == '__main__':
    start()
