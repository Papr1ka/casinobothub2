"""
Ког, обрабатывающий команды:
    - custom
    - give
    - godboard
    - offer
    - pay
    - reply
    - stats
    - status
    - scoreboard
    - theme
"""

from discord import Member, Embed, File, Colour, Client
from discord.ext.commands import is_owner, has_permissions, Cog, command, guild_only, Context
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import cooldown, max_concurrency
from logging import config, getLogger
from math import ceil
from os import remove

from database import db
from discord_components.client import DiscordComponents
from handlers import MailHandler
from main import on_command
from models.card import Card
from models.errors import NotEnoughMoney, InvalidUser
from models.pagi import Paginator
from models.user_model import UserModel
from models.shop import shop_id

config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())



class UserStats(Cog):
    """
    Ког, обрабатывающий команды:
        - custom
        - give
        - godboard
        - offer
        - pay
        - reply
        - stats
        - status
        - scoreboard
        - theme
    """
    def __init__(self, Bot: Client):
        self.Bot = Bot
        logger.info(f"{__name__} Cog has initialized")
    
    @command(
        usage="`=status @(user)`",
        help="Получить карточку пользователя"
    )
    @guild_only()
    async def status(self, ctx: Context, member: Member = None):
        """
        Команда status
        Если опыта достаточно, повышает уровень
        Создаёт изображение, называемое карточкой пользователя с его индивидуальной информацией,
        такой как опыт, уровень, роль, описание и имя
        Отправляет изображение в контекстный канал, после чего удаляет

        Для карточки существует 2 темы
        Функционал карточки реализуется в models.Card

        Аргументы:
            ctx: Context - контекст вызова команды
            member: Member | None - пользователь, чью карточку необходимо создать
        """
        await on_command(self.Bot.get_command('status'))
        if member is None:
            member = ctx.author
        
        user = await db.fetch_user(ctx.guild.id, member.id, exp=1, level=1, custom=1, color=1)

        _, new_exp, new_level, exp_to_next_level = await self.__update_check_level(ctx.guild_id, member.id, user['exp'], user['level'])
        user['exp'] = new_exp
        user['level'] = new_level
        user['exp_to_next_level'] = exp_to_next_level

        # Добавляется дополнительная информация для отображения
        role = member.top_role
        user['top_role'] = role.name[1:] if role.name.startswith('@') else role.name
        if user['top_role'] == 'everyone':
            if user['color'] == 'dark':
                user['role_color'] = (255, 255, 255)
            else:
                user['role_color'] = role.colour.to_rgb()
        else:
            user['role_color'] = role.colour.to_rgb()
        user['avatar'] = member.avatar_url_as(format='webp', size=256).__str__()
        user['username'] = member.name

        # Создание карты, card - относительный путь файла
        card = await Card(user).render_get()
        # Отправка
        await ctx.send(file=File('./' + card))
        # Удаление файла
        remove('./' + card)
    
    async def __update_check_level(self, guild_id: int, user_id: int, current_exp: int, current_level: int):
        """
        Метод повышает уровень пользователя, если хватает опыта, иначе ничего не делает

        Аргументы:
            guild_id: int - айди гильдии
            user_id: int - айди пользователя
            current_exp: int - текущий опыт пользователя
            current_level: int - текущий уровень пользователя
        
        Возвращает:
            Tuple(
                money: int - количество денег, выданное пользователю за повышение уровня
                new_exp: int - новый опыт пользователя
                new_level: int - новый уровень пользователя
                exp_tp_next_level: int - количество опыта, необходимое для повышение уровня пользователя
            )
        """
        new_exp, new_level, exp_to_next_level = UserModel.exp_to_level(current_exp, current_level)
        money = 0
        if current_level < new_level:
            while current_level < new_level:
                money += UserModel.only_exp_to_level(current_level)
                current_level += 1
            
            await db.update_user(guild_id, user_id, {'$inc': {'money': money}, '$set': {'exp': new_exp, 'level': new_level}})
        return money, new_exp, new_level, exp_to_next_level
    
    @command(
        usage="`=stats @(user)`",
        help="Получить статистику пользователя"
    )
    @guild_only()
    async def stats(self, ctx: Context, member: Member = None):
        """
        Команда stats
        Если опыта достаточно, повышает уровень
        Выводит статистику о пользователе в виде Embed-а
        Деньги, сообщения, количество сыгранных игр, аватар, имя
        
        Аргументы:
            ctx: Context - контекст вызова команды
            member: Member | None - пользователь, чью карточку необходимо создать
        """
        await on_command(self.Bot.get_command('stats'))
        if member is None:
            member = ctx.author
        user = await db.fetch_user(ctx.guild.id, member.id, money=1, messages=1, games=1, exp=1, level=1)

        money, _, _, _ = await self.__update_check_level(ctx.guild.id, member.id, user['exp'], user['level'])

        user['money'] += money
        embed = Embed(title = member.name + '#' + member.discriminator)
        embed.add_field(name='Денег', value=user['money'])
        embed.add_field(name='Сообщений', value=user['messages'])
        embed.add_field(name='Игр сыграно', value=user['games'])
        embed.set_author(name='Статистика')
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)
    
    @command(
        usage="`=theme`",
        help="Изменить тему для карточки пользователя на противоположную (light / dark)"
    )
    @guild_only()
    async def theme(self, ctx: Context):
        """
        Команда theme
        Изменяет тему пользователя на противоположную
        С тёмной на светлую, со светлой на тёмную
        После чего отправляет Embed сообщение, информирующее об изменении темы

        Аргументы:
            ctx: Context - контекст вызова команды
        """
        await on_command(self.Bot.get_command('theme'))
        theme = await db.fetch_user(ctx.guild.id, ctx.author.id, color=1)
        theme = theme['color']
        if theme == 'dark':
            theme = 'light'
        else:
            theme = 'dark'
        await db.update_user(ctx.guild.id, ctx.author.id, {'$set': {'color': theme}})
        embed = Embed(
            title=f'Тема установлена на {theme.upper()}',
            color=Colour.dark_theme()
        )
        await ctx.reply(embed=embed)
    
    @command(
        usage="`=custom [описание]`",
        help="Изменить описание для карточки пользователя"
    )
    @guild_only()
    async def custom(self, ctx: Context, *args):
        """
        Команда custom
        Изменяет статус пользователя
        После чего отправляет Embed сообщение, информирующее о его изменении

        Аргументы:
            ctx: Context - контекст вызова команды
            args: List[str] - значение, если не указан, используется значение UserModel.__CUSTOM по умолчанию
        """
        await on_command(self.Bot.get_command('custom'))
        custom = ' '.join(args)
        if len(custom) > 0:
            custom = custom[:19]
        else:
            custom = UserModel.get_custom()
        await db.update_new(ctx.guild.id, ctx.author.id, {'$set': {'custom': custom}})
        title = f'Описание установлена на {custom}'
        embed = Embed(
            title=title,
            color=Colour.dark_theme()
        )
        await ctx.reply(embed=embed)
    
    @staticmethod
    async def transaction(fromaddr: tuple, toaddr: tuple, amount: int):
        """
        Метод переводит amount денег со счёта fromaddr на счёт toaddr
        Не проверяет операцию на согласованность (все проверки вовне)
        Аргументы:
            fromaddr: Tuple(guild_id: int, member_id: int) - айди гильдии, айди пользователя,
            toaddr: Tuple(guild_id: int, member_id: int) - айди гильдии, айди пользователя,
            amount: int - количество переводимых средств
        """
        query = [
            [fromaddr[0], fromaddr[1], {'$inc': {'money': -amount}}],
            [toaddr[0], toaddr[1], {'$inc': {'money': amount}}]
        ]
        await db.update_many(query)

    @command(
        usage="`=pay @[user] [сумма]`",
        help="Перевести сумму денег со своего счёта на счёт пользователя"
    )
    @guild_only()
    async def pay(self, ctx: Context, member: Member, amount: int):
        """
        Команда pay
        Переводит amount (> 0) денег со счёта пользователя, вызвавшего команду на счёт пользователя member

        Аргументы:
            ctx: Context - контекст вызова команды
            member: Member - адресат
            amount: int - количество переводимых средств
        """
        await on_command(self.Bot.get_command('pay'))
        if amount > 0:
            if not member is None:
                from_wallet = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1)
                from_wallet = from_wallet['money']
                if amount <= from_wallet:
                    await self.transaction((ctx.guild.id, ctx.author.id), (member.guild.id, member.id), amount)
                    embed = Embed(title=f"`{amount}$` переведено на счёт {member.nick if member.nick else member.name}")
                    await ctx.send(embed=embed)
                else:
                    raise NotEnoughMoney(f'{(ctx.author.nick if not ctx.author.nick is None else ctx.author.name) + "#" + ctx.author.discriminator}, недостаточно средств')
            else:
                raise InvalidUser('Некорректный адресат')
        else:
            embed = Embed(title=f"{amount}$ ? Ты платить собирался, или как?", color=Colour.dark_theme())
            await ctx.send(embed=embed)
    
    @command(
        usage="`=give @[user] [сумма]`",
        help="Перевести сумму денег на счёт пользователя",
        brief="administrator"
    )
    @has_permissions(administrator=True)
    @guild_only()
    async def give(self, ctx: Context, member: Member, amount: int):
        """
        Команда pay
        Админская команда, переводит amount на счёт пользователя member, amount может быть меньше 0

        Аргументы:
            ctx: Context - контекст вызова команды
            member: Member - адресат
            amount: int - количество переводимых средств
        """
        await on_command(self.Bot.get_command('give'))
        if not member is None:
            # ограничения базы данных (максимальное число - int64), если прописать команду give @user 2^56 2^8 раз,
            # команда напишет, что деньги переведены, но это будет неправдой, потому что у поля базы данных произойдёт переполнение
            # в длинной арифметике смысла нету, оптимальнее установить ограничение и модифицировать команду, чтобы оповещала о переполнении кошелька
            if amount < (2 ** 56):
                await db.update_new(member.guild.id, member.id, {'$inc': {'money': amount}})
                embed = Embed(title=f"`{amount}$` переведено на счёт {member.nick if member.nick else member.name}")
            else:
                embed = Embed(title=f"У банка нет таких средств, попробуйте быть поскромнее")
            await ctx.send(embed=embed)
        else:
            raise InvalidUser('Некорректный адресат')
    
    
    @command(
        usage="`=offer [идея]`",
        help="Отправить предложение по улучшению работы бота, или внедрению новых возможностей"
    )
    async def offer(self, ctx: Context, *, message):
        """
        Команда offer
        Бот принимает сообщение от пользователя и отправляет создателю, задумывается как канал для отправки идей для улучшения

        Аргументы:
            ctx: Context - контекст вызова команды
            message: str - сообщение
        """
        await on_command(self.Bot.get_command('offer'))
        if message:
            owner = await self.Bot.application_info()
            await owner.owner.send(f"Предложение от {ctx.author.name}#{ctx.author.discriminator}: {message}, message_id={ctx.author.id}")
            await ctx.send(embed=Embed(title='Предложение отправлено', color=Colour.dark_theme()))
        else:
            await ctx.send(embed=Embed(title='Ваше предложение малосодержательное', color=Colour.dark_theme()))

    @command(
        usage="Знать не положено",
        help="Знать не положено"
    )
    @is_owner()
    async def reply(self, ctx, user_id: int, *, message):
        """
        Команда reply
        Команда для создателя бота, позволяет создателю отправлять сообщение пользователю бота по id
        задумывается как способ ответа на предложение через offer

        Аргументы:
            ctx: Context - контекст вызова команды
            user_id: int - айди пользователя
            message: str - сообщение
        """
        await on_command(self.Bot.get_command('reply'))
        try:
            user = await self.Bot.fetch_user(user_id)
        except:
            await ctx.send(embed=Embed(title='пользователь не найден', color=Colour.dark_theme()))
        else:
            await user.send('Ответ на ваше предложение: ' + message)
            await ctx.send(embed=Embed(title='ответ отправлен', color=Colour.dark_theme()))
            
    async def exp_sum(self, level: int):
        """
        Метод подсчёта суммарного опыта, переведённого в уровни

        Аргументы:
            level: int - уровень пользователя
        
        Возвращает:
            exp: int - уровень пользователя в опыте
        """
        if level == 1:
            return 0
        return UserModel.only_exp_to_level(level) + await self.exp_sum(level - 1)
    
    
    @command(
        usage="`=scoreboard`",
        help="Топ участников сервера по опыту"
    )
    @max_concurrency(1, BucketType.member, wait=False)
    @cooldown(1, 60, BucketType.member)
    @guild_only()
    async def scoreboard(self, ctx: Context):
        """
        Команда scoreboard
        Отправляет пагинатор с всеми зарегистрированными в боте участниками сервера, их уровнями, опытом и кастомным описанием,
        отсортированном по убыванию согласно суммарному опыту

        Аргументы:
            ctx: Context - контекст вызова команды
        """
        await on_command(self.Bot.get_command('scoreboard'))
        # Получение всех участников гильдии одним запросом
        q = db.db[await db.get_shard(ctx.guild.id)].aggregate([
            {'$match': {'_id': {'$ne': shop_id(ctx.guild.id)}, 'guild_id': ctx.guild.id}},
            {'$project': {'_id': 1, 'custom': 1, 'level': 1, 'exp': 1}},
        ])
      
        # Создание ключа сортировки
        q = await q.to_list(length=None)
        for i in range(len(q)):
            q[i]['ex'] = await self.exp_sum(q[i]['level']) + q[i]['exp']
        
        # сортировка
        l = len(q)
        users = sorted(q, key=lambda item: item['ex'])[::-1]
        
        # подготовка embed объектов для пагинатора
        embeds = [Embed(title=f'Рейтинг участников {ctx.guild.name}', color=Colour.dark_theme()) for i in range(ceil(l / 10))]
        # отправка пагинатора
        s = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=str(ctx.message.id) + "pagi1100022", values=users, guild=ctx.guild, forse=10, timeout=300)
        await s.send()

    
    @command(
        usage="`=godboard`",
        help="Топ участников сервера по состоятельности"
    )
    @max_concurrency(1, BucketType.member, wait=False)
    @cooldown(1, 60, BucketType.member)
    @guild_only()
    async def godboard(self, ctx):
        """
        Команда scoreboard
        Отправляет пагинатор с всеми зарегистрированными в боте участниками сервера, их средствами и кастомными описаниями,
        отсортированном по убыванию согласно деньгам

        Аргументы:
            ctx: Context - контекст вызова команды
        """
        await on_command(self.Bot.get_command('godboard'))
        # Получение всех участников гильдии одним запросом
        q = db.db[await db.get_shard(ctx.guild.id)].aggregate([
            {'$match': {'_id': {'$ne': shop_id(ctx.guild.id)}, 'guild_id': ctx.guild.id}},
            {'$project': {'_id': 1, 'custom': 1, 'money': 1}},
        ])
      
        q = await q.to_list(length=None)
        # Сортировка
        l = len(q)
        users = sorted(q, key=lambda item: item['money'])[::-1]
        
        # подготовка embed объектов для пагинатора
        embeds = [Embed(title=f'Самые богатые участники {ctx.guild.name}', color=Colour.dark_theme()) for i in range(ceil(l / 10))]
        # отправка пагинатора
        s = Paginator(DiscordComponents(self.Bot), ctx.channel.send, embeds, author_id=ctx.author.id, id=str(ctx.message.id) + "pagi1100022", values=users, guild=ctx.guild, t=2, timeout=300, forse=10)
        r = await s.send()
    

def setup(Bot):
    # Функция, необходимая для инициализации кога, вызывается в main при load_extension
    Bot.add_cog(UserStats(Bot))

transaction = UserStats.transaction
