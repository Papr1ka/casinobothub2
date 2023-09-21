"""
Главный файл бота, точка входа
"""

from asyncio import sleep
from discord import Member, Embed, Intents, Guild
from discord.colour import Colour
from discord.ext.commands import AutoShardedBot as Robot, Context, Command
from discord.ext.commands.core import guild_only, is_owner
from discord.errors import HTTPException
from handlers import MailHandler
from json import loads
from logging import config, getLogger
from math import ceil
from time import time

from .database import db
from .discord_components import DiscordComponents, Button, ButtonStyle
from .models.fishing import wshop
from .settings import TOKEN, SHARD_COUNT


"""
Документация discord.py
https://discordpy.readthedocs.io/en/latest/api.html
"""

# Добавление логгера для текущего файла
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

# Привилегии бота
ints = Intents(guilds=True, members=True, guild_messages=True, guild_reactions=True)

# Создание экземпляров классов бота дискорд (шардированного (читать в документации discord про AutoShardedBot))
Token = TOKEN
Bot = Robot(shard_count=SHARD_COUNT, command_prefix="=", intents=ints)
# Оболочка для работы пакета discord_components
DBot = DiscordComponents(Bot)

# Буферный список гильдий, в которых уже есть экземпляры ботов casino, про использование читать в on_guild_join и on_guild_remove
bad_guilds = []
# Айди экземпляров ботов казино
bot_ides = [883201346759704606, 936355038245302292]

@Bot.event
async def on_ready():
    """
    Сообщение бота о готовности к работе
    """
    logger.info("bot is started")


@Bot.event
async def on_guild_join(guild: Guild):
    """
    Событие добавления бота в гильдию
    
    Корутина добавляет запись в базу данных, либо отсоединяет бота от гильдии, если найден другой его экземпляр

    Аргументы:
        guild: discord.Guild - гильдия, к которой присоединился бот
    """
    logger.info(f"bot joined guild: region - {guild.region} | name - {guild.name} | members - {guild.member_count}")
    can_connect = True
    # Проверяем, есть ли в гильдии другой экземпляр бота
    for i in bot_ides:
        # Отбрасываем текущий экземпляр, смотрим только другие
        if i != Bot.user.id:
            try:
                # Пытаемся найти другой экземпляр
                bot = await guild.fetch_member(i)
            except HTTPException:
                # Не нашли
                pass
            else:
                # Нашли
                can_connect = False
                break
        
    if not can_connect:
        """
        Если нашли другой экземпляр бота в гильдии
        Добавляем в буфер, так как далее бот отсоединится от сервера
        (На сервере не может быть более 1 бота казино)
        Чтобы при on_guild_remove не удалять гильдию из базы данных,
        ведь экземпляр который мы обнаружили будет и дальше работать на сервере
        (База данных одна для всех экземпляров бота)
        """
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
        # Если наш экземпляр на сервере первый, то магазин
        await db.create_shop(guild.id)

@Bot.event
async def on_guild_remove(guild: Guild):
    """
    Событие удаления бота из гильдии

    Корутина либо удаляет запись из базы данных, либо ничего не делает

    Аргументы:
        guild: discord.Guild - гильдия, из которой вышел бот
    """
    logger.info(f"bot removed from guild: region - {guild.region} | name - {guild.name} | members - {guild.member_count}")
    # Если это был единственный экземпляр в гильдии, то удаляем информацию о ней в базе данных 
    if guild.id not in bad_guilds:
        await db.remove_guild(guild.id)
    else:
        # Если это был второй или более экземпляр, то гильдию из базы данных мы не удаляем (пускай 1-й экземпляр и дальше работает)
        bad_guilds.remove(guild.id)

@Bot.event
async def on_member_remove(member: Member):
    """
    Событие выхода пользователя из гильдии

    Корутина удаляет информацию о пользователе из базы данных НА ОПРЕДЕЛЁННОМ СЕРВЕРЕ

    Аргументы:
        member: discord.Member - пользователь, вышедший из гильдии
    """
    await db.delete_user(member.guild.id, member.id)

Bot.remove_command('help')

@Bot.command()
async def help(ctx: Context, module_command=None):
    """
    Обработчик команды помощи

    Корутина выводит справку либо об имеющихся модулях,
    либо о командах внутри одного модуля, либо справку об отдельной команде

    Аргументы:
        ctx: discord.ext.commands.Context - контекст вызова программы
        module_command:str = None - название модуля или команды для выдачи справки
    """
    await on_command(Bot.get_command('help'))
    # Список модулей
    modules = ('casino', 'user', 'store', 'fishing', 'admin')
    embed = Embed(color=Colour.dark_theme())

    # Если просят справку об имеющихся модулях
    if not module_command:
        embed.title=f"{Bot.user.name} модули"
        embed.add_field(name='Казино', value='`=help casino`', inline=True)
        embed.add_field(name='Пользовательское', value='`=help user`', inline=True)
        embed.add_field(name='Магазин', value='`=help store`', inline=True)
        embed.add_field(name='Рыбалка', value='`=help fishing`', inline=True)
        embed.add_field(name='Настройка', value='`=help admin`', inline=True)
    else:
        # Если просят справку об отдельном модуле
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
            # Если просят справку об отдельной команде, находим её
            for i in Bot.commands:
                if i.name == module_command:
                    break
            
            # Если команды не существует
            if i.name != module_command:
                embed.title = "Команда не найдена"
            else:
                # Выводим справку об отдельной команде
                # Справка задаётся в Bot.command декораторе
                embed.title = i.name
                embed.add_field(name='Использование', value=i.usage, inline=False)
                embed.description = i.help
                if i.brief:
                    embed.add_field(name="Полномочия", value=i.brief)
    
    await ctx.send(embed=embed)


async def on_command(command: Command):
    """
    Обработчик всех команд

    Нужен для отладки и аналитики в будущем

    Аргументы:
        command: discord.ext.command.Command
    """
    logger.info(command)

#Bot.loop.create_task(data.loop())


@Bot.command(
    help="Проголосуйте за бота и получите 3 подарочных коробки! (раз в 12 часов)",
    usage="`=vote`"
)
@guild_only()
async def vote(ctx: Context):
    """
    Команда голосования за бота на сайте top.gg

    Корутина либо выдаёт информационное сообщение, 
    либо начисляет пользователю 3 подарочных коробки за голосование

    Аргументы:
        ctx: discord.ext.commands.Context - контекст вызова программы
    """
    await on_command(Bot.get_command('vote'))

    # Запрашиваем информацию о голосовании пользователя
    status, r = await db.dblget_user_vote(ctx.author.id)
    embed = Embed(title=ctx.author.display_name, color=Colour.dark_purple())
    if status == 200:
        voted = False if not r['voted'] else True
        if voted:
            # Пользователь проголосовал
            # present будет равен Подарочной коробке под номером 10001, см. models/fishing, словарь boxes
            present = wshop[10001]
            # Вытягиваем из базы данных последнее время голосования пользователя
            last_vote = await db.fetch_user(ctx.guild.id, ctx.author.id, claim=1)
            last_vote = last_vote['claim']
            now_time = time()
            if last_vote != 0:
                diff = now_time - last_vote
                if diff >= 43200:
                    # Если пользователь голосовал более 12ч тому назад, то начисляем коробки
                    embed.title = "**Спасибо за голос! Начислено: `3 подарочных коробки`** Голосуйте снова через 12ч"
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$set': {'claim': now_time},
                                                                   '$push': {f'inventory': {'$each': [{
                        'name': present.name,
                        'cost': present.cost,
                        'description': present.description,
                        'loot': present.loot,
                        'url': present.url,
                        'tier': present.tier
                        } for i in range(3)]}}}) # В количестве 3-х штук
                else:
                    # Если пользователь голосовал в последние 12 часов, говорим ему время ожидания до следующей возможности
                    diff = 43200 - diff
                    h = int(diff // 3600)
                    m = ceil((diff - h * 3600) / 60)
                    embed.title = f"**Вы уже получили награду, голосуйте через {h} часов, {m} минут!**"
            else:
                # Пользователь ранее никогда не голосовал, начисляем коробки
                embed.title = "**Спасибо за голос! Начислено: `3 подарочных коробки`** Голосуйте снова через 12ч"
                await db.update_user(ctx.guild.id, ctx.author.id, {'$set': {'claim': now_time},
                                                                   '$push': {f'inventory': {'$each': [{
                        'name': present.name,
                        'cost': present.cost,
                        'description': present.description,
                        'loot': present.loot,
                        'url': present.url,
                        'tier': present.tier
                        } for i in range(3)]}}})
        else:
            embed.title = "**Чтобы получить награду, проголосуйте на сайте и напишите `=vote`**"
            embed.url = 'https://top.gg/bot/883201346759704606/vote'
    elif status == 401:
        # Проблема с аутентификации на top.gg
        logger.error(f"Topgg auth if failed; {r}")
        embed.title = "Обратитесь позже"
    else:
        # Проблемы на серверах top.gg
        logger.error(f"Topgg search failed, status:{r.status}; {r}")
        embed.title = "Сервера сайта недоступны, обратитесь позже"
    await ctx.send(embed=embed)


@Bot.command()
@is_owner()
async def announcement(ctx: Context, *, annonce: str):
    """
    Админская команда уведомления о новости

    Аргументы:
        ctx: discord.ext.commands.Context - контекст вызова программы
        annonce: str - Строка Embed-а новости в формате json, удобно создать в discord embed generator-ах
    """
    print(annonce)
    logger.info("Announcement: sending started")
    send = 0
    annonce = loads(annonce)
    embed = Embed.from_dict(annonce)
    for guild in Bot.guilds:
        try:
            # Если в гильдии установлен системный канал (куда по умолчанию отправляются сообщения о приветствии новых пользователей от discord)
            # То отправляем туда новость
            channel = guild.system_channel
            if not channel is None:
                await channel.send(embed=embed)
                send += 1
        except Exception as E:
            # Недостаточно прав или что-либо ещё
            logger.warning(E)
            
    logger.info(f"Announcement was sent, received by servers: {send}")


@Bot.command()
@is_owner()
async def add(ctx: Context):
    """
    Админская команда добавления индексов

    Добавляет на всех коллекциях базы данных интекс `guild_id`,
    следует делать это не средствами бота, а например в docker

    Аргументы:
        ctx: discord.ext.commands.Context - контекст вызова программы
    """
    logger.info("Add command started")
    for i in range(100):
        await db.db[f'shard{i}'].create_index('guild_id')
    logger.info("Add command completed")

@Bot.command(
    help="Постоянная ссылка на наш сайт",
    usage="`=url`"
)
async def url(ctx: Context):
    """
    Команда для получения ссылки на сайт

    Отправляет в текущий канал сообщение с ссылкой на сайт

    Аргументы:
        ctx: discord.ext.commands.Context - контекст вызова программы

    [Сайт не работает]
    """
    embed = Embed(title="Смотрите команды и следите за новостями на нашем сайте!", color=Colour.dark_theme())
    components = [Button(label='Наш сайт', url='https://casino-web.herokuapp.com/casino/', style=ButtonStyle.URL)]
    await ctx.send(embed=embed, components=components)


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
