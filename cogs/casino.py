from asyncio import sleep
from random import randint
from discord.errors import NotFound
from discord.ext.commands import guild_only, Cog, command
from discord import Embed, Colour, Member
from logging import config, getLogger
from time import time

from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import max_concurrency
from discord.ext.commands.errors import BadArgument

from database import db
from discord_components import Button, ButtonStyle
from cogs.error_handler import ErrorHandler
from cogs.leveling import LevelTable
from handlers import MailHandler
from main import on_command
from models.colode import *
from models.rulet import Rulet
from models.slots import Slots, emoji
import models.errors as errors
from asyncio import TimeoutError as TError


config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class Casino(Cog):

    __rulet_fields = [
        {
            'inline': True,
            'name': 'на цвет',
            'value': 'выйгрыш 1 к 1'
        },
        {
            'inline': True,
            'name': 'на чётность',
            'value': 'выйгрыш 1 к 1'
        },
        {
            'inline': True,
            'name': 'на половину',
            'value': 'выйгрыш 1 к 1'
        },
        {
            'inline': True,
            'name': 'на дюжину',
            'value': 'выйгрыш 2 к 1'
        },
        {
            'inline': True,
            'name': 'на линию',
            'value': 'выйгрыш 2 к 1'
        },
        {
            'inline': True,
            'name': 'на число',
            'value': 'выйгрыш 35 к 1'
        }
    ]

    __rulet_emojis = [
        '⬅️',
        '🔳',
        '➡️',
        '⏬',
        '🔽',
        '➖',
        '➕',
        '🔼',
        '⏫',
        '🎰'
    ]

    __bets_type = [
        'на цвет',
        'на чётность',
        'на половину',
        'на линию',
        'на дюжину',
        'на число'
    ]

    __bets_type_len = __bets_type.__len__()

    __bets = {
        'на цвет': ['на красное', 'на чёрное'],
        'на чётность': ['на чётное', 'на нечётное'],
        'на половину': ['на 1-18', 'на 19-36'],
        'на линию': ['линия 1', 'линия 2', 'линия 3'],
        'на дюжину': ['дюжина 1', 'дюжина 2', 'дюжина 3'],
        'на число': ["на " + i.__str__() for i in range(0, 37)]
    }

    __rps_emoji = {
        1: "🥌",
        2: "✂️",
        3: "🧻"
    }
    
    __messages = {} #{message_id: {'message': discord.Message, 'author': str, 'bet_type': int, 'bet': int, 'bet_type_type': int, 'author_id': int, 'choice': bool, 'mobile': bool, 'author_money': int, 'guild_id': int, 'last_use': time.time}}
    __games = {
        #{'channel_id': []}
    }
    __bet_kf = {
        '⏬': -1000,
        '🔽': -100,
        '➖': -10,
        '➕': 10,
        '🔼': 100,
        '⏫': 1000,
    }
    __min_bet = 100
    __max_bet = 10000
    __max_games = 2
    __sleep = 300 #300

    __vnumbers = {
        '1': '1️⃣',
        '2': '2️⃣',
        '3': '3️⃣',
        '4': '4️⃣',
        '5': '5️⃣',
        '6': '6️⃣',
        '7': '7️⃣',
        '8': '8️⃣',
        '9': '9️⃣',
        '0': '0️⃣',
    }

    __vcolors = {
        'red': '🟥',
        'black': '⬛️',
        'null': '🟩'
    }
    
    __paddings = {
        1: (27, 27), #14, 11
        2: (18, 17),
        3: (23, 23),
        4: 74,
        5: 42,
        6: (27, 27)
    }

    def __init__(self, Bot): 
        self.Bot = Bot
        logger.info(f"{__name__} Cog has initialized")
    
    def __set_bet(self, money, increase, aviable):
        sm = money + increase
        if self.__min_bet <= sm <= self.__max_bet:
            if sm <= aviable:
                return sm
            return aviable
        elif sm < self.__min_bet:
            if self.__min_bet <= aviable:
                return self.__min_bet
            return aviable
        else:
            if self.__max_bet <= aviable:
                return self.__max_bet
            return aviable

    async def __emoji_handler(self, payload):
        e = payload.emoji.__str__()
        try:
            msg = self.__messages[payload.message_id]
        except:
            channel = self.Bot.get_channel(payload.channel_id)
            #await ErrorHandler.on_error(channel=channel, error=errors.BadGamesession("Сессия устарела"))
        else:
            if msg['author_id'] != payload.user_id:
                return
            message = msg['message']
            embed = Embed(
                title = "Рулетка",
                colour = Colour.dark_teal()
            )
            embed._fields = self.__rulet_fields
            embed.set_image(url='https://game-wiki.guru/content/Games/ruletka-11-pole.jpg')
            if e == "⬅️":
                logger.debug('editing bet_type: -1')
                msg['bet_type'] = (msg['bet_type'] - 1) % self.__bets_type_len
                msg['choice'] = False
            elif e == "➡️":
                logger.debug('editing bet_type: +1')
                msg['bet_type'] = (msg['bet_type'] + 1) % self.__bets_type_len
                msg['choice'] = False
            elif e == "🔳":
                logger.debug('editing bet_type_type')
                msg['bet_type_type'] = (msg['bet_type_type'] + (1 if msg['choice'] else 0)) % self.__bets[self.__bets_type[msg['bet_type']]].__len__()
                msg['choice'] = True
            elif e in ('⏬', '🔽', '➖', '➕', '🔼', '⏫'):
                logger.debug('editing money')
                msg['bet'] = self.__set_bet(msg['bet'], self.__bet_kf[e], msg['author_money'])
            else:
                if not msg['choice']:
                    await ErrorHandler.on_error(channel=message.channel, error=errors.NotSelectedBetType(f'{msg["author"]}, не выбран тип ставки'))
                else:
                    msg['bet'] = self.__set_bet(msg['bet'], 0, msg['author_money'])
                    if msg['bet'] >= self.__min_bet:
                        if self.__can_roll(message.channel.id, message.id):
                            await self.__roll(msg)
                        else:
                            await ErrorHandler.on_error(channel=message.channel, error=errors.TooManyGames(f'подождите, идёт игра'))
                    else:
                        await ErrorHandler.on_error(channel=message.channel, error=errors.NotEnoughMoney(f'{msg["author"]}, недостаточно средств'))

            
            bet_type = self.__bets_type[msg['bet_type']] if not msg['choice'] else self.__bets[self.__bets_type[msg['bet_type']]][msg['bet_type_type']]
            msg['last_use'] = time()
            self.__messages[message.id] = msg
            description = self.__format_description(msg['mobile'], msg['author'], msg['bet'], bet_type=bet_type)
            embed.description = description
            await message.edit(embed=embed)
    
    async def __deleter_old_games(self):
        while not self.Bot.is_closed():
            games = self.__messages.keys()
            to_remove = []
            for i in games:
                if time() - self.__messages[i]['last_use'] > self.__sleep:
                    to_remove.append(i)
            for i in to_remove:
                self.__messages.pop(i)
                logger.debug(f"removed old game {i}")
            await sleep(self.__sleep)


    def __getspaces(self, on_mobile: bool, bet_type_len: int, spin: bool):
        if on_mobile:
            if spin:
                starts = self.__paddings[6]
            else:
                starts = self.__paddings[1]
        else:
            if spin:
                starts = self.__paddings[3]
            else:
                starts = self.__paddings[2]
        diff = bet_type_len - 6
        if diff % 2 == 0:
            return (starts[0] - diff // 2, starts[1] - diff // 2)
        else:
            return (starts[0] - diff // 2  - 1, starts[1] - diff // 2)
    
    def __format_description(self, on_mobile, name, money, bet_type = "Ставки", spin = False):
        spaces = self.__getspaces(on_mobile, bet_type.__len__(), spin)
        description = f"{name[:spaces[0]]: <{spaces[0]}} |  {bet_type}  | {money: >{spaces[1]}}$"
        if not on_mobile:
            description = '```elixir\n' + description + '```'
        else:
            description = '**' + description + '**'
        return description + '\n'

    @command(
        usage='`=rulet`',
        help=f"Контроллеры:\n⬅️ - Изменить вид ставки, скролл налево\n➡️ - Изменить вид ставки, скролл налево\n🔳 - Выбрать тип ставки\n⏬ - понизить ставку на 1000$\n🔽 - понизить ставку на 100$\n➖ - понизить ставку на 10$\n➕ - повысить ставку на 10$\n🔼 - повысить ставку на 100$\n⏫ - повысить ставку на 100$\n🎰 - крутить рулетку\nМинимальная ставка - {__min_bet}\nМаксимальная ставка - {__max_bet}\nОграничения - 2 ролла на канал"
    )
    @guild_only()
    async def rulet(self, ctx):
        await on_command(self.Bot.get_command('rulet'))
        user = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1)
        money = user['money']
        if money < self.__min_bet:
            raise errors.NotEnoughMoney(f'{ctx.author.name}, недостаточно средств')

        embed = Embed(
            title = "Рулетка",
            description = self.__format_description(ctx.author.is_on_mobile(), ctx.author.name, self.__min_bet.__str__()),
            colour = Colour.dark_teal()
        )
        embed._fields = self.__rulet_fields
        embed.set_image(url='https://game-wiki.guru/content/Games/ruletka-11-pole.jpg')
        message = await ctx.send(embed=embed)
        self.__messages[message.id] = {
            'message': message,
            'author': ctx.author.name,
            'bet_type': 0,
            'bet': self.__min_bet,
            'bet_type_type': 0,
            'author_id' : ctx.author.id,
            'choice': False,
            'mobile': ctx.author.is_on_mobile(),
            'author_money': money,
            'guild_id': ctx.guild.id,
            'last_use': time()
        }
        for emoji in self.__rulet_emojis:
            await message.add_reaction(emoji)
    
    def __visualize_number(self, number):
        out = '0️⃣' if number < 10 else ''
        for i in number.__str__():
            out += self.__vnumbers[i]
        return out
    
    def __get_win(self, bet_type_type, win, number):
        if bet_type_type in self.__bets['на цвет']:
            if bet_type_type == "на красное":
                return {'win': win[0] == "red", 'kf': 2}
            return {'win': win[0] == "black", 'kf': 2}
        elif bet_type_type in self.__bets['на чётность']:
            if bet_type_type == "на чётное":
                return {'win': win[1] == "even", 'kf': 2}
            return {'win': win[1] == "odd", 'kf': 2}
        elif bet_type_type in self.__bets['на половину']:
            if bet_type_type == "на 1-18":
                return {'win': 1 <= number <= 18, 'kf': 2}
            return {'win': 19 <= number <= 36, 'kf': 2}
        elif bet_type_type in self.__bets['на линию']:
            return {'win': int(bet_type_type[6]) == win[2], 'kf': 3}
        elif bet_type_type in self.__bets['на дюжину']:
            return {'win': (int(bet_type_type[7]) - 1) * 12 < number <= int(bet_type_type[7]) * 12, 'kf': 3}
        elif bet_type_type in self.__bets['на число']:
            return {'win': int(bet_type_type[3:]) == number, 'kf': 36}
        return {'win': False, 'kf': 0}
    
    def __format_footer(self, won, bet):
        if won > 0:
            return f"вы выиграли {won}$"
        return f"вы проиграли {bet}$"
        
    def __can_roll(self, channel_id, message_id):
        try:
            games = self.__games[channel_id]
        except KeyError:
            self.__games[channel_id] = [message_id]
            return True
        else:
            if games.__len__() < self.__max_games:
                if games.count(message_id) < 1:
                    if self.__games[channel_id].__len__() == 0:
                        self.__games[channel_id] = [message_id]
                    else:
                        self.__games[channel_id].append(message_id)
                    return True
                return False
            return False


    async def __roll(self, msg):
        bet = msg['bet']
        await db.update_user(msg['guild_id'], msg['author_id'], {'$inc': {'money': -bet, 'games': 1}})
        self.__messages[msg['message'].id]['author_money'] -= bet
        message = msg['message']
        channel = message.channel
        increase = - bet
        padding = self.__paddings[4] if not msg['mobile'] else self.__paddings[5]
        step = 9 if not msg['mobile'] else 7
        bet_type = self.__bets_type[msg['bet_type']] if not msg['choice'] else self.__bets[self.__bets_type[msg['bet_type']]][msg['bet_type_type']]
        description = self.__format_description(msg['mobile'], msg['author'], bet, bet_type=bet_type)
        embed = Embed()
        game = Rulet(step=step)
        rolls = game.spin()
        first_numbers = next(rolls)
        embed.add_field(name=f"```{'♥️':-^{padding}}```", value='```elixir\n' + '  '.join([self.__visualize_number(i) for i in first_numbers]) + '\n' + '  '.join([self.__vcolors[game.check(i)[0]] * 2 for i in first_numbers]) + '```')
        description = self.__format_description(msg['mobile'], msg['author'], bet, bet_type=bet_type, spin=True)
        embed.description = description
        message = await channel.send(embed=embed)
        for i in game.spin():
            final = i
            embed.clear_fields()
            embed.add_field(name=f"```{'♥️':-^{padding}}```", value='```elixir\n' + '  '.join([self.__visualize_number(number) for number in i]) + '\n' + '  '.join([self.__vcolors[game.check(number)[0]] * 2 for number in i]) + '```')
            await sleep(1)
            try:
                await message.edit(embed=embed)
            except NotFound:
                await db.update_user(msg['guild_id'], msg['author_id'], {'$inc': {'money': bet}})
                await ErrorHandler.on_error(channel=channel, error=errors.BadGamesession("Игра была прервана, ставка возвращена"))
                self.__games[channel.id].remove(msg['message'].id)
                self.__messages[msg['message'].id]['author_money'] += bet
                return
        
        win_ind = step // 2
        win = game.check(final[win_ind])
        win = self.__get_win(self.__bets[self.__bets_type[msg['bet_type']]][msg['bet_type_type']], win, final[win_ind])
        won = bet * (win['kf'] if win['win'] else 0)
        increase += won
        await db.update_user(msg['guild_id'], msg['author_id'], {'$inc': {'money': bet + increase, 'games': 1}})
        embed.set_footer(text=self.__format_footer(won - bet, bet))
        try:
            await message.edit(embed=embed)
        except NotFound:
            await db.update_user(msg['guild_id'], msg['author_id'], {'$inc': {'money': bet}})
            await ErrorHandler.on_error(channel=channel, error=errors.BadGamesession("Игра была прервана, ставка возвращена"))
            self.__games[channel.id].remove(msg['message'].id)
            self.__messages[msg['message'].id]['author_money'] += bet
            return
        self.__games[channel.id].remove(msg['message'].id)
        self.__messages[msg['message'].id]['author_money'] += won

    
    async def closeGame(self, author_id, guild_id):
            games = self.__messages.keys()
            to_remove = []
            for i in games:
                if self.__messages[i]['author_id'] == author_id and self.__messages[i]['guild_id'] == guild_id:
                    to_remove.append(i)
            for i in to_remove:
                self.__messages.pop(i)
                logger.debug(f"removed old game {i}")
    
    @command(
        usage='`=blackjack [ставка] (тайм-аут в секундах)`',
        help=f"Правила казино:\nСплит делается 1 раз\nКомбинации не оплачиваются\nСтраховка не разрешена\nБлэкджек оплачивается в конце игры\nБлэкджек дилера не вскрывается\nПачка из 6 колод\nправила классического блэкджека"
    )
    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    async def blackjack(self, ctx, bet: int, timeout: int=60):
        await on_command(self.Bot.get_command('blackjack'))
        await self.closeGame(ctx.author.id, ctx.guild.id)
        if timeout < 15 or timeout > 300:
            await ctx.reply(embed=Embed(title="Неверный таймаут, укажите в множестве [15-300]", color=Colour.dark_theme()))
            return
        author_money = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1)
        author_money = author_money['money']
        if bet < self.__min_bet or bet > self.__max_bet:
            await ctx.reply(embed=Embed(title=f"Ставка должна быть в диапазоне [{self.__min_bet}, {self.__max_bet}]$", color=Colour.dark_theme()))
            return
        if author_money < bet:
            raise errors.NotEnoughMoney(f'{(ctx.author.nick if ctx.author.nick else ctx.author.name) + "#" + ctx.author.discriminator}, недостаточно средств')
        await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': -bet}})
        def check(interaction):
            return (interaction.custom_id[-1:-6:-1][::-1] in ('bjoin', 'start')) and interaction.channel == ctx.channel and interaction.user.id not in game.reg[1:]
        
        def check2(interaction):
            return (interaction.custom_id[-1:-10:-1][::-1] in ('hit______', 'stand____', 'split____', 'double___', 'surrender')) and interaction.channel == ctx.channel and interaction.user.id in game.reg and sum(game.played[interaction.user.id]) >= 1
        

        game = Game(bet)
        await game.add_player(ctx.author.id, (ctx.author.nick if ctx.author.nick else ctx.author.name) + "#" + ctx.author.discriminator, author_money - bet)
        
        embed = Embed(title=f"`Блэкджек | Ставка {bet}$ | @{(ctx.author.nick if ctx.author.nick else ctx.author.name)}`")
        embed.description = f"`Игроки: {len(game.players)}`"
        embed.add_field(name="🕵️‍♂️ "+game.players[ctx.author.id][0].name, value=f"`{game.players[ctx.author.id][0].bet}$`")
        embed.set_footer(text=f'Ожидание игроков, игра начнётся через {timeout} секунд')
        
        c_id = str(ctx.message.id)
        bs_buttons = [
            Button(label="Старт", style=ButtonStyle.green, custom_id=c_id + "start"),
            Button(label="Присоединиться", style=ButtonStyle.blue, custom_id=c_id + "bjoin"),
        ]
        
        controller = await ctx.send(embed=embed, components=bs_buttons)
        start = time()
        timeout2 = timeout
        
        while time() - start < timeout:
            try:
                interaction = await self.Bot.wait_for('button_click', timeout=timeout - (time() - start), check=check)
            except:
                pass
            else:
                if interaction.user.id == game.reg[0]:
                    if interaction.custom_id[-1:-6:-1][::-1] == 'start':
                        timeout = 0
                else:
                    money = await db.fetch_user(ctx.guild.id, interaction.user.id, money=1)
                    money = money['money']
                    if money >= bet:
                        
                        await game.add_player(interaction.user.id, (interaction.user.nick if interaction.user.nick else interaction.user.name) + "#" + interaction.user.discriminator, money - bet)
                        await db.update_user(ctx.guild.id, interaction.user.id, {'$inc': {'money': -bet}})
                        embed.description = f"`Игроки: {len(game.players)}`"
                        embed.set_footer(text=f'Ожидание игроков, игра начнётся через {int(timeout - (time() - start))} секунд')
                        embed.add_field(name="🕵️‍♂️ "+game.players[interaction.user.id][0].name, value=f"`{game.players[interaction.user.id][0].bet}$`", inline=False)
                        await interaction.edit_origin(embed=embed)
                    else:
                        await interaction.respond(embed=Embed(title=f'{(interaction.user.nick if interaction.user.nick else interaction.user.name) + "#" + interaction.user.discriminator}, недостаточно средств', color=Colour.dark_theme()))
        
        await game.create_dealer()
        
        embed.clear_fields()
        
        embed.add_field(name="🔴 " +game.dealer.name, value=f"`{game.dealer.bet}$`             {c[game.dealer.hand[0]]}", inline=False)
        
        for player_id in game.reg:
            await game.give_cards(player_id, 2)
            player = game.players[player_id][await game.getCurrPlayerInd(player_id)]

            embed.add_field(name="🔴 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
            
    
        embed.description = "`hit` - взять ещё одну карту\n`stand` - больше не брать карт\n`split` - разбить руку на две\n`double` - удвоить ставку, и взять 1 карту\n`surrender` - сдаться\n"
        embed.set_footer(text=f"Игра идёт, до конца осталось {timeout2} с")
        blackjack_buttons = [
            [Button(label='hit', style=ButtonStyle.blue, custom_id=c_id + "hit______"),
            Button(label='stand', style=ButtonStyle.green, custom_id=c_id + "stand____"),
            Button(label='split', style=ButtonStyle.blue, custom_id=c_id + "split____"),
            Button(label='double', style=ButtonStyle.green, custom_id=c_id + "double___"),
            Button(label='surrender', style=ButtonStyle.green, custom_id=c_id + "surrender")]
        ]
        
        await interaction.edit_origin(embed=embed, components=blackjack_buttons)
        start = time()
        
        
        while (time() - start < timeout2) and sum([sum(i) for i in game.played.values()]) != 0:
            try:
                interaction = await self.Bot.wait_for('button_click', timeout=timeout2 - (time() - start), check=check2)
            except:
                pass
            else:
                player = game.players[interaction.user.id][await game.getCurrPlayerInd(interaction.user.id)]

                if interaction.custom_id[-1:-10:-1][::-1] == 'hit______':
                    if player.cards >= 1:
                        player = await game.give_cards(interaction.user.id, 1)
                        if player.sm() > 21:
                            for i in range(len(embed.fields)):
                                if player.name in embed.fields[i].name and embed.fields[i].name.startswith("🔴"):
                                    embed.set_field_at(
                                        index=i, name="🟢 " +player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False
                                    )
                                    break
                            
                            player = await game.end_move(interaction.user.id)
                        else:
                            for i in range(len(embed.fields)):
                                if player.name in embed.fields[i].name and embed.fields[i].name.startswith("🔴"):
                                    embed.set_field_at(
                                        index=i, name="🔴 " +player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False
                                    )
                                    break
                    else:
                        await interaction.respond(embed=Embed(color=Colour.dark_theme(), title="Вы не можете взять карту, так как ранее вы удваивали"))
                elif interaction.custom_id[-1:-10:-1][::-1] == 'stand____':
                    for i in range(len(embed.fields)):
                        if player.name in embed.fields[i].name and embed.fields[i].name.startswith("🔴"):
                            embed.set_field_at(
                                index=i, name="🟢 " +player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False
                            )
                            break
                    
                    player = await game.end_move(interaction.user.id)
                
                elif interaction.custom_id[-1:-10:-1][::-1] == 'split____':
                    if len(player.hand) == 2:
                        if points[player.hand[0]] == points[player.hand[1]]:
                            if player.split is False:
                                if player.money >= game.bet:
                                    await db.update_user(ctx.guild.id, interaction.user.id, {'$inc': {'money': -bet}})
                                    pl2 = await game.split(interaction.user.id)
                                    
                                    for i in range(len(embed.fields)):
                                        if player.name in embed.fields[i].name and embed.fields[i].name.startswith("🔴"):
                                            embed.set_field_at(
                                                index=i, name="🔴 " +player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in pl2[0].hand])}", inline=False
                                            )
                                            break
                                    embed.add_field(name="🔴 " +player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in pl2[1].hand])}", inline=False)
                                else:
                                    await ErrorHandler.on_error(channel=interaction.channel, error=errors.NotEnoughMoney(f'{(interaction.user.nick if interaction.user.nick else interaction.user.name) + "#" + interaction.user.discriminator}, недостаточно средств'))
                            else:
                                await interaction.respond(embed=Embed(color=Colour.dark_theme(), title="Вы уже делали сплит"))
                        else:
                            await interaction.respond(embed=Embed(color=Colour.dark_theme(), title="Вы не можете сделать сплит"))
                    else:
                        await interaction.respond(embed=Embed(color=Colour.dark_theme(), title="Вы не можете сделать сплит"))
                        
                        
                elif interaction.custom_id[-1:-10:-1][::-1] == 'double___':
                    if player.cards > 1:
                        if player.money >= bet:
                            await db.update_user(ctx.guild.id, interaction.user.id, {'$inc': {'money': -bet}})
                            player = await game.double(interaction.user.id)
                            
                            for i in range(len(embed.fields)):
                                if player.name in embed.fields[i].name and embed.fields[i].name.startswith("🔴"):
                                    embed.set_field_at(
                                        index=i, name="🟢 " +player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False
                                    )
                                    break
                        else:
                            await ErrorHandler.on_error(channel=interaction.channel, error=errors.NotEnoughMoney(f'{(interaction.user.nick if interaction.user.nick else interaction.user.name) + "#" + interaction.user.discriminator}, недостаточно средств'))
                    else:
                        await interaction.respond(embed=Embed(color=Colour.dark_theme(), title="Вы уже удваивали"))
                elif interaction.custom_id[-1:-10:-1][::-1] == 'surrender':
                    if len(player.hand) == 2:
                        player = await game.surrender(interaction.user.id)
                        for i in range(len(embed.fields)):
                            if player.name in embed.fields[i].name and embed.fields[i].name.startswith("🔴"):
                                embed.set_field_at(
                                    index=i, name="🟢 " +player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False
                                )
                                break
                    else:
                        await interaction.respond(embed=Embed(color=Colour.dark_theme(), title="Сдаться можно только с рукой в 2 карты"))
                
                embed.set_footer(text=f"Игра идёт, до конца осталось {int(timeout2 - (time() - start))} с")
                await interaction.edit_origin(embed=embed)
        embed.set_footer(text=f"Игра")
        
        d_points = await game.count_dealer()
        embed.clear_fields()
        
        embed.add_field(name=game.dealer.name, value=f"`{game.dealer.bet}$`             {' , '.join([c[x] for x in game.dealer.hand])}", inline=False)
        
        query = []
        footer = 'Результаты игры:\n'
        
        for i in game.players.values():
            for player in i:
                summa = player.sm()
                if player.surrender is True:
                    embed.add_field(name="💸 " + player.name, value=f"`{int(player.bet / 2)}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                    query.append(
                        [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': int(player.bet / 2)}}]
                    )
                    footer += f'{player.name} : сдался\n'
                else:
                    if summa > 21:
                        embed.add_field(name="💸 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                        #проигрыш
                        query.append(
                            [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1}}]
                        )
                        footer += f'{player.name} : проигрыш\n'
                    elif d_points > 21:
                        if summa == 21:
                            if len(player.hand) == 2:
                                embed.add_field(name="🤑 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                                #блэкджек
                                query.append(
                                    [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': player.bet + int(player.bet * 1.5)}}]
                                )
                                footer += f'{player.name} : блэкджек\n'
                            else:
                                embed.add_field(name="💰 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                                #победа
                                query.append(
                                    [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': int(player.bet * 2)}}]
                                )
                                footer += f'{player.name} : победа\n'
                        else:
                            embed.add_field(name="💰 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                            #победа
                            query.append(
                                [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': int(player.bet * 2)}}]
                            )
                            footer += f'{player.name} : победа\n'
                    elif summa == d_points:
                        if len(player.hand) == 2 and len(game.dealer.hand) > 2 and summa == 21:
                            embed.add_field(name="🤑 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                            #блэкджек
                            query.append(
                                [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': player.bet + int(player.bet * 1.5)}}]
                            )
                            footer += f'{player.name} : блэкджек\n'
                        elif len(game.dealer.hand) == 2 and len(player.hand) > 2 and summa == 21:
                            embed.add_field(name="💸 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                            #проигрыш
                            query.append(
                                [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1}}]
                            )
                            footer += f'{player.name} : проигрыш\n'
                        else:
                            embed.add_field(name="🟨 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                            #ничья
                            query.append(
                                [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': player.bet}}]
                            )
                            footer += f'{player.name} : ничья\n'
                    elif summa == 21:
                        if len(player.hand) == 2:
                            embed.add_field(name="🤑 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                            #блэкджек
                            query.append(
                                [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': player.bet + int(player.bet * 1.5)}}]
                            )
                            footer += f'{player.name} : блэкджек\n'
                        else:
                            embed.add_field(name="💰 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                            #победа
                            query.append(
                                [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': int(player.bet * 2)}}]
                            )
                            footer += f'{player.name} : победа\n'
                    elif summa < 21 and summa > d_points:
                        embed.add_field(name="💰 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                        #победа
                        query.append(
                            [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1, 'money': int(player.bet * 2)}}]
                        )
                        footer += f'{player.name} : победа\n'
                    else:
                        embed.add_field(name="💸 " + player.name, value=f"`{player.bet}$`             {' , '.join([c[x] for x in player.hand])}", inline=False)
                        #проигрыш
                        query.append(
                            [ctx.guild.id, player.id, {'$inc': {'exp': LevelTable['casino'], 'games': 1}}]
                        )
                        footer += f'{player.name} : проигрыш\n'
        
        embed.set_footer(text=footer)
        await controller.edit(embed=embed, components=[])
        await db.update_many(query)


    @command(
        usage="`=slots [ставка]`",
        help=f"Выйгрыши, суммируются, формируется по формуле - `тип выйгрыша` * `тип предметов`\n3 в ряд или по диагонали\nКоэффициент - 1\n4 в ряд\nКоэффициент - 1.5\n5 в ряд\nКоэффициент - 2\n{str(emoji[1])}\nКоэффициент - 0.5\n{str(emoji[2])}\nКоэффициент - 0.75\n{str(emoji[3])}\nКоэффициент - 1\n{str(emoji[4])}\nКоэффициент - 1.25\n{str(emoji[5])}\nКоэффициент - 1.5\nОграничения - 2 ролла на канал"
    )
    @guild_only()
    @max_concurrency(2, BucketType.channel, wait=False)
    async def slots(self, ctx, bet: int):
        await on_command(self.Bot.get_command('slots'))
        await self.closeGame(ctx.author.id, ctx.guild.id)
        if bet > self.__max_bet or bet < self.__min_bet:
            await ctx.send(embed=Embed(title=f"Ставка должна быть в диапазоне [{self.__min_bet}, {self.__max_bet}]$", color=Colour.dark_theme()))
            return
        money = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1)
        money = money['money']
        if money < bet:
            raise errors.NotEnoughMoney(f'{(ctx.author.nick if ctx.author.nick else ctx.author.name) + "#" + ctx.author.discriminator}, недостаточно средств')
        else:
            await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': -bet}})
        embed = Embed(title = "Слоты", color = Colour.dark_theme())
        embed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = "https://cdn.iconscout.com/icon/free/png-512/casino-chance-gamble-gambling-roulette-table-wheel-4-17661.png")
        lines = ["☠️☠️☠️☠️☠️", "☠️☠️☠️☠️☠️", "☠️☠️☠️☠️☠️"]
        for l in range(3):
            lines[l] = " ".join(list(lines[l]))
        embed.description = "".join([i + "\n" for i in lines])
        game = await ctx.send(embed = embed)
        roll = Slots().spin(bet)
        for i in range(5):
            await sleep(1)
            for lin in range(3):
                lines[lin] = lines[lin][:i * 2] + str(emoji[roll[1][i + lin * 5]]) + " " + lines[lin][(i + 2) * 2:]
            description = "".join([i + "\n" for i in lines])
            embed.description = description
            await game.edit(embed = embed)
        embed.set_footer(text = ("Вы потеряли" if roll[0] - bet < 0 else "Вы выиграли") + " " + str(abs(int(roll[0] - bet))) + " $", icon_url = "https://image.flaticon.com/icons/png/512/8/8817.png")
        await game.edit(embed = embed)
        await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': int(roll[0])}})


    @slots.error
    async def on_slots_error(self, ctx, error):
        if isinstance(error, BadArgument):
            embed = Embed(title="Ставка должна быть в диапазоне [100, 1000]", color=Colour.dark_theme())
            await ctx.send(embed=embed)
    
    async def rollTheDice(self):
        return randint(1, 6), randint(1, 6)

    async def rollRPS(self):
        return [randint(1, 3), randint(1, 3)]
    
    @command(
        usage="`=dice [ставка] (@оппонент)`",
        help="Выигрывает тот, кому выпадет большее число"
    )
    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    async def dice(self, ctx, bet: int, member: Member=None):
        await on_command(self.Bot.get_command('dice'))
        await self.closeGame(ctx.author.id, ctx.guild.id)
        if bet > self.__max_bet or bet < self.__min_bet:
            await ctx.send(embed=Embed(title=f"Ставка должна быть в диапазоне [{self.__min_bet}, {self.__max_bet}]$", color=Colour.dark_theme()))
            return
        money = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1)
        money = money['money']
        if money < bet:
            raise errors.NotEnoughMoney(f'{(ctx.author.nick if ctx.author.nick else ctx.author.name) + "#" + ctx.author.discriminator}, недостаточно средств')
        else:
            embed = Embed(color = Colour.dark_theme())
            embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
            if member is None:
                await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': -bet }})
                embed.title = f"{ctx.author.display_name} vs King Dice!"
                embed.set_thumbnail(url = "https://i.pinimg.com/originals/a0/39/f0/a039f043d0c0089a203fc3b974081496.png")
                win = await self.rollTheDice()
                embed.title = f"{ctx.author.display_name} : {emomoji[win[0]]} vs {emomoji[win[1]]} : King Dice"
                dic = await ctx.send(embed = embed)
                if win[0] > win[1]:
                    description = f"{ctx.author.display_name} выйграл! {bet}$"
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet * 2}})
                elif win[0] == win[1]:
                    description = f"ничья"
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                else:
                    description = f"King Dice выйграл! {bet}$"
                await sleep(1)
                embed.set_footer(text = description)
                await dic.edit(embed = embed)
            else:
                if member.id != ctx.author.id and not member.bot:
                    c_id = str(ctx.message.id)
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': -bet }})
                    components = [Button(label="Играть", style=ButtonStyle.green, custom_id=c_id + 'acceptdice')]
                    await ctx.send(f"{member.mention}, {ctx.author.display_name} приглашает вас в сыграть в кости, ставка `{bet}$`, осталось `60` секунд", components=components)

                    def check(inter):
                        return inter.custom_id == c_id + 'acceptdice' and inter.channel.id == ctx.channel.id and inter.user.id == member.id

                    try:
                        interaction = await self.Bot.wait_for('button_click', timeout=60, check=check)
                    except TError:
                        await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                        embed = Embed(title="Никто не присоединился", color=Colour.dark_theme())
                        await ctx.send(embed=embed)
                        return
                    else:
                        member_money = await db.fetch_user(ctx.guild.id, member.id, money=1)
                        member_money = member_money['money']
                        if member_money < bet:
                            await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                            raise errors.NotEnoughMoney(f'{(member.nick if member.nick else member.name) + "#" + member.discriminator}, недостаточно средств')
                        else:
                            await db.update_user(ctx.guild.id, member.id, {'$inc': {'money': -bet }})
                            embed.title = f"{ctx.author.display_name} vs {member.display_name}!"
                            embed.set_thumbnail(url = interaction.user.avatar_url)
                            win = await self.rollTheDice()
                            embed.title = f"{ctx.author.display_name} : {emomoji[win[0]]} vs {emomoji[win[1]]} : {member.display_name}"
                            dic = await interaction.edit_origin(embed=embed, components=[])
                            if win[0] > win[1]:
                                description = f"{ctx.author.display_name} выйграл! {bet}$"
                                await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet * 2 }})
                            elif win[0] == win[1]:
                                description = f"ничья!"
                                await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                                await db.update_user(ctx.guild.id, member.id, {'$inc': {'money': bet }})
                            else:
                                description = f"{member.display_name} выйграл! {bet}$"
                                await db.update_user(ctx.guild.id, member.id, {'$inc': {'money': bet * 2}})
                            await sleep(1)
                            embed.set_footer(text = description)
                            await dic.edit(embed=embed, components=[])
                else:
                    embed = Embed(title="Вы не можете играть с самим собой или с другим ботом")
                    await ctx.reply(embed = embed)
                
    
    @dice.error
    async def on_dice_error(self, ctx, error):
        if isinstance(error, BadArgument):
            embed = Embed(title="Ставка должна быть в диапазоне [100, 1000]", color=Colour.dark_theme())
            await ctx.send(embed=embed)
    
    
    @command(
        usage="`=rps [ставка] (@оппонент)`",
        help="Камень ломает ножницы, ножницы разрезают бумагу, бумага обёртывает камень"
    )
    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    async def rps(self, ctx, bet: int, member: Member = None):
        await on_command(self.Bot.get_command('rps'))
        await self.closeGame(ctx.author.id, ctx.guild.id)
        c_id = str(ctx.message.id)
        if bet > self.__max_bet or bet < self.__min_bet:
            await ctx.send(embed=Embed(title=f"Ставка должна быть в диапазоне [{self.__min_bet}, {self.__max_bet}]$", color=Colour.dark_theme()))
            return
        money = await db.fetch_user(ctx.guild.id, ctx.author.id, money=1)
        money = money['money']
        if money < bet:
            raise errors.NotEnoughMoney(f'{(ctx.author.nick if ctx.author.nick else ctx.author.name) + "#" + ctx.author.discriminator}, недостаточно средств')
        else:
            embed = Embed(color = Colour.dark_theme())
            embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
            if member is None:
                await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': -bet }})
                embed.set_thumbnail(url = "https://i.pinimg.com/originals/a0/39/f0/a039f043d0c0089a203fc3b974081496.png")
                embed.title = f"{ctx.author.display_name} vs King Dice"
                win = await self.rollRPS()
                components = [[Button(label="Камень", style=ButtonStyle.blue, custom_id=c_id + 'rock'),
                               Button(label="Ножницы", style=ButtonStyle.blue, custom_id=c_id + 'scissors'),
                               Button(label="Бумага", style=ButtonStyle.blue, custom_id=c_id + 'paper')]]
                origin = await ctx.send(embed=embed, components=components)
                def check1(inter):
                    return (inter.custom_id == c_id + 'rock' or inter.custom_id == c_id + 'scissors' or inter.custom_id == c_id + 'paper') and inter.channel.id == ctx.channel.id and inter.user.id == ctx.author.id
                try:
                    interaction = await self.Bot.wait_for('button_click', timeout=60, check=check1)
                except TError:
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                    embed = Embed(title="Нет ответа", color=Colour.dark_theme())
                    await ctx.send(embed=embed)
                    return
                else:
                    if interaction.custom_id == c_id + 'rock':
                        win[0] = 1
                    elif interaction.custom_id == c_id + 'scissors':
                        win[0] = 2
                    else:
                        win[0] = 3
                
                embed.title = f"{ctx.author.display_name} : {self.__rps_emoji[win[0]]} vs {self.__rps_emoji[win[1]]} : King Dice"
                dic = await interaction.edit_origin(embed=embed, components=[])
                if (win[0] == 1 and win[1] == 2) or (win[0] == 2 and win[1] == 3) or (win[0] == 3 and win[1] == 1):
                    description = f"{ctx.author.display_name} выйграл! {bet}$"
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet * 2}})
                elif win[0] == win[1]:
                    description = f"ничья"
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                else:
                    description = f"King Dice выйграл! {bet}$"
                await sleep(1)
                embed.set_footer(text = description)
                await dic.edit(embed=embed, components=[])
            else:
                if member.id != ctx.author.id and not member.bot:
                    await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': -bet }})
                    components = [Button(label="Играть", style=ButtonStyle.green, custom_id=c_id + 'claimrps')]
                    await ctx.send(f"{member.mention}, {ctx.author.display_name} приглашает вас в сыграть в Камень, Ножницы, Бумага, ставка `{bet}$`, осталось `60` секунд", components=components)

                    def check(inter):
                        return inter.custom_id == c_id + 'claimrps' and inter.channel.id == ctx.channel.id and inter.user.id == member.id

                    try:
                        interaction = await self.Bot.wait_for('button_click', timeout=60, check=check)
                    except TError:
                        await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                        embed = Embed(title="Никто не присоединился", color=Colour.dark_theme())
                        await ctx.send(embed=embed)
                        return
                    else:
                        member_money = await db.fetch_user(ctx.guild.id, member.id, money=1)
                        member_money = member_money['money']
                        if member_money < bet:
                            await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                            raise errors.NotEnoughMoney(f'{(member.nick if member.nick else member.name) + "#" + member.discriminator}, недостаточно средств')
                        else:
                            await db.update_user(ctx.guild.id, member.id, {'$inc': {'money': -bet }})
                            embed.title = f"{ctx.author.display_name} vs {member.display_name}!"
                            embed.set_thumbnail(url = interaction.user.avatar_url)
                            
                            
                            components = [[Button(label="Камень", style=ButtonStyle.blue, custom_id=c_id + 'rock'),
                               Button(label="Ножницы", style=ButtonStyle.blue, custom_id=c_id + 'scissors'),
                               Button(label="Бумага", style=ButtonStyle.blue, custom_id=c_id + 'paper')]]
                            origin = await interaction.edit_origin(embed=embed, components=components)
                            def check2(inter):
                                return (inter.custom_id == c_id + 'rock' or inter.custom_id == c_id + 'scissors' or inter.custom_id == c_id + 'paper') and inter.channel.id == ctx.channel.id and (inter.user.id == ctx.author.id or inter.user.id == member.id)
                            sm = 0
                            win = await self.rollRPS()
                            while sm < 2:
                                try:
                                    interaction = await self.Bot.wait_for('button_click', timeout=60, check=check2)
                                except TError:
                                    await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                                    embed = Embed(title="Никто не присоединился", color=Colour.dark_theme())
                                    await ctx.send(embed=embed)
                                    return
                                else:
                                    if interaction.custom_id == c_id + 'rock':
                                        if interaction.user.id == ctx.author.id:
                                            win[0] = 1
                                        else:
                                            win[1] = 1
                                    elif interaction.custom_id == c_id + 'scissors':
                                        if interaction.user.id == ctx.author.id:
                                            win[0] = 2
                                        else:
                                            win[1] = 2
                                    else:
                                        if interaction.user.id == ctx.author.id:
                                            win[0] = 3
                                        else:
                                            win[1] = 3
                                    sm += 1
                                    if sm < 2:
                                        await interaction.respond(embed=Embed(title="Ждём ответа соперника...", color=Colour.dark_theme()))
                            
                            
                            embed.title = f"{ctx.author.display_name} : {self.__rps_emoji[win[0]]} vs {self.__rps_emoji[win[1]]} : {member.display_name}"
                            await origin.edit(embed=embed, components=[])
                            if (win[0] == 1 and win[1] == 2) or (win[0] == 2 and win[1] == 3) or (win[0] == 3 and win[1] == 1):
                                description = f"{ctx.author.display_name} выйграл! {bet}$"
                                await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet * 2 }})
                            elif win[0] == win[1]:
                                description = f"ничья!"
                                await db.update_user(ctx.guild.id, ctx.author.id, {'$inc': {'money': bet }})
                                await db.update_user(ctx.guild.id, member.id, {'$inc': {'money': bet }})
                            else:
                                description = f"{member.display_name} выйграл! {bet}$"
                                await db.update_user(ctx.guild.id, member.id, {'$inc': {'money': bet * 2}})
                            await sleep(1)
                            embed.set_footer(text=description)
                            await origin.edit(embed=embed, components=[])
                else:
                    embed = Embed(title="Вы не можете играть с самим собой или с другим ботом")
                    await ctx.reply(embed=embed)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        logger.debug('reaction added')
        if payload.emoji.__str__() in self.__rulet_emojis and not payload.member.bot:
            await self.__emoji_handler(payload)
    
    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        logger.debug('reaction removed')
        if payload.emoji.__str__() in self.__rulet_emojis:
            await self.__emoji_handler(payload)
    
    @Cog.listener()
    async def on_ready(self):
        self.Bot.loop.create_task(self.__deleter_old_games())



def setup(Bot):
    Bot.add_cog(Casino(Bot))