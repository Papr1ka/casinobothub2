"""
Файл, описывающий инструменты для работы команды blackjack
"""

from random import choice

# Колода на 52 карты
c = {
    1: '2❤️',
    2: '2♦️',
    3: '2♠',
    4: '2♣',
    5: '3❤️',
    6: '3♦️',
    7: '3♠',
    8: '3♣',
    9: '4❤️',
    10: '4♦️',
    11: '4♠',
    12: '4♣',
    13: '5❤️',
    14: '5♦️',
    15: '5♠',
    16: '5♣',
    17: '6❤️',
    18: '6♦️',
    19: '6♠',
    20: '6♣',
    21: '7❤️',
    22: '7♦️',
    23: '7♠',
    24: '7♣',
    25: '8❤️',
    26: '8♦️',
    27: '8♠',
    28: '8♣',
    29: '9❤️',
    30: '9♦️',
    31: '9♠',
    32: '9♣',
    33: '10❤️',
    34: '10♦️',
    35: '10♠',
    36: '10♣',
    37: 'J❤️',
    38: 'J♦️',
    39: 'J♠',
    40: 'J♣',
    41: 'Q❤️',
    42: 'Q♦️',
    43: 'Q♠',
    44: 'Q♣',
    45: 'K❤️',
    46: 'K♦️',
    47: 'K♠',
    48: 'K♣',
    49: 'T❤️',
    50: 'T♦️',
    51: 'T♠',
    52: 'T♣',
}


# Количество очков, которое даёт карта из c, сопоставление 1 к 1
points = {
    1 : 2,
    2 : 2,
    3 : 2,
    4 : 2,
    5 : 3,
    6 : 3,
    7 : 3,
    8 : 3,
    9 : 4,
    10 : 4,
    11 : 4,
    12 : 4,
    13 : 5,
    14 : 5,
    15 : 5,
    16 : 5,
    17 : 6,
    18 : 6,
    19 : 6,
    20 : 6,
    21 : 7,
    22 : 7,
    23 : 7,
    24 : 7,
    25 : 8,
    26 : 8,
    27 : 8,
    28 : 8,
    29 : 9,
    30 : 9,
    31 : 9,
    32 : 9,
    33 : 10,
    34 : 10,
    35 : 10,
    36 : 10,
    37 : 10,
    38 : 10,
    39 : 10,
    40 : 10,
    41 : 10,
    42 : 10,
    43 : 10,
    44 : 10,
    45 : 10,
    46 : 10,
    47 : 10,
    48 : 10,
    49 : 11,
    50 : 11,
    51 : 11,
    52 : 11,
}

# Для игры в blackjack используются 6 колод, это пачка
col = [i for i in range(1, 53)] * 6

emomoji = {
    1 : "1️⃣",
    2 : "2️⃣",
    3 : "3️⃣",
    4 : "4️⃣",
    5 : "5️⃣",
    6 : "6️⃣"
}

class Player():
    """
    Класс игрока, создаётся во время работы команды blackjack
    и предназначен для использования в рамках 1-й раздачи
    """
    def __init__(self, name: str, bet: int, money: int, id: int) -> None:
        """
        Аргументы:
            name: str - имя игрока
            bet: int - ставка игрока
            money: int - количество денег игрока
            id: int - айди игрока (пользователя)
        """
        self.name = name
        self.bet = bet
        # Делал ли игрок сплит
        self.split = False
        self.cards = 9999999999
        self.money = money
        # Завершил ли игрок свой ход
        self.end = False
        # Карты в руке игрока
        self.hand = []
        self.id = id
        # Сдался ли игрок
        self.surrender = False
    
    def __str__(self) -> str:
        return f"name: {self.name}; bet: {self.bet}; split: {self.split}; cards: {self.cards}; money: {self.money}; end: {self.end}; hand: {self.hand}; surrender: {self.surrender}"

    def __repr__(self) -> str:
        return self.__str__()
    
    def from_dict(self, inf):
        """
        Метод, создающий объект игрока из словаря
        """
        a = Player(inf['name'], inf['bet'], inf['money'], inf['id'])
        a.split = inf['split']
        a.cards = inf['cards']
        a.end = inf['end']
        a.hand = inf['hand']
        a.id = inf['id']
        a.surrender = inf['surrender']
        return a
    
    def sm(self):
        """
        Метод, считающий сумму очков в руке игрока
        """
        s = 0
        tuz = []
        for i in self.hand:
            if points[i] == 11:
                tuz.append(i)
            s += points[i]
            if s > 21 and tuz:
                tuz.pop(0)
                s -= 10
        return s

class Game():
    """
    Класс для реализации раздачи в блекджеке, рассчитан на использование в рамках 1-й раздачи
    """
    
    def __init__(self, bet: int) -> None:
        """
        Аргументы:
            bet: int - общая для 1-го стола ставка
        """
        # игроки
        self.players = {}
        # словарь Dict[id: int, List[int]] - айди пользователю соответствует список из 1-го или 2-х элементов,
        # если значение в списке 1, значит у пользователя есть право ходить, если 0, то он уже сыграл
        # если список из 2-х элементов, значит игрок сделал сплит и считается как 2 игрока
        self.played = {}
        # айди пользователей, севших за стол
        self.reg = []
        # ставка стола
        self.bet = bet
        # пачка стола
        self.colode = col.copy()
        # дилер
        self.dealer: Player
    
    async def add_player(self, id: int, name: str, money: int):
        """
        Метод добавления игрока в список участников стола

        Аргументы:
            id: int - айди пользователя
            name: str - имя пользователя
            money: int - количество денег пользователя
        """
        # Добавление в словарь игроков стола
        self.players[id] = [Player(name, self.bet, money, id)]
        # Разрешение игроку ходить
        self.played[id] = [1]
        # Регистрация участника за столом
        self.reg.append(id)
    
    async def get_card(self):
        """
        Метод получения новой карты из пачки

        Возвращает:
            card: int - номер карты, ключ к c, points
        """
        card = choice(self.colode)
        self.colode.remove(card)
        return card
    
    async def give_cards(self, player_id: int, amount: int):
        """
        Метод, выдающий пользователю с id=player_id amount карт

        Аргументы:
            player_id: int - айди пользователя
            amount: int - количество карт, которые нужно раздать пользователю
        
        Возвращает:
            player: Player - объект игрока с обновлённой рукой
        """
        index = await self.getCurrPlayerInd(player_id)
        hand = []
        for i in range(amount):
            hand.append(
                await self.get_card()
            )
            self.players[player_id][index].cards -= 1
        hand.extend(self.players[player_id][index].hand)
        await self.change(player_id, index, hand=hand)
        return self.players[player_id][index]
    
    async def getCurrPlayerInd(self, id):
        """
        Возвращает первого из игроков, под id=id, если игрок сделал сплит, то игроков за столом под 1-м id двое,
        этот метод возвращает индекс первого игрока с возможностью хода из двух, иначе None
        
        Пример: Игрок сделал сплит, потом hit, индекс будет 0-й, потом он завершит ход,
        чтобы операции далее производились с вторым игроком, должен быть возвращён 1-й индекс

        Возвращает:
            i: int | None - индекс игрока в списке players, который должен ходить
        """
        for i in range(len(self.players[id])):
            if self.players[id][i].end is False:
                return i
        return None
    
    async def create_dealer(self):
        """
        Метод создания дилера стола
        """
        self.dealer = Player(
            "👤 Дилер",
            self.bet,
            99999999999999,
            None
        )
        self.dealer.hand.append(await self.get_card())
        self.dealer.hand.append(await self.get_card())
        
    async def change(self, id: int, index: int, **arg: dict):
        """
        Метод, заменяющий объект игрока на новый, который создаётся с новыми данными
        Этот метод требовал дополнительной отладки, так как при изменении значения поля объекта изменения не происходили
        Работает, не трогать без должного понимания

        Аргументы:
            id: int - айди пользователя
            index: int - индекс игрока под id пользователя
            args: Dict[str, Any] - словарь значений, требующих изменения
        """
        self.players[id][index] = self.players[id][index].from_dict(
            {
                'name': self.players[id][index].name,
                'money': self.players[id][index].money,
                'bet': self.players[id][index].bet,
                'split': self.players[id][index].split,
                'cards': self.players[id][index].cards,
                'end': self.players[id][index].end,
                'hand': self.players[id][index].hand,
                'id': self.players[id][index].id,
                'surrender': self.players[id][index].surrender,
                **arg
            }
        )
        
    async def end_move(self, id: int, s: bool=False):
        """
        Метод, завершающий ход игрока

        Аргументы:
            id: int - айди пользователя
            s: bool - сдался ли игрок
        
        Возвращает:
            player: Player - объект игрока
        """
        index = await self.getCurrPlayerInd(id)
        self.played[id][index] -= 1
        await self.change(id, index, end=True, surrender=s)
        return self.players[id][index]
    
    async def split(self, id: int):
        """
        Метод, соответствующих действию игрока под названием split, разделяет руку игрока поровну и добавляет по 1-й новой карте каждому
        Каждому игроку предоставляется независимая возможность ходить при том, что игроков представляет 1 пользователь

        Команда не проверяет право на split согласно правилам blackjack, это делается вовне

        Аргументы:
            id: int - айди пользователя
        
        Возвращает:
            List[Player] - список игроков под айди пользователя
        """
        index = await self.getCurrPlayerInd(id)
        player = self.players[id][index]
        player.split = True

        # Теперь игроков 2-е
        self.players[id] = [player, player]
        self.played[id] = [1, 1]

        hand1 = [player.hand[0], await self.get_card()]
        hand2 = [player.hand[1], await self.get_card()]
        await self.change(id, 0, hand=hand1)
        await self.change(id, 1, hand=hand2)
        return self.players[id]

    async def double(self, id):
        """
        Метод, соответствующих действию игрока под названием double, удваивает ставку пользователя

        Команда не проверяет право на double согласно правилам blackjack, это делается вовне, команда автоматически завершает ход игрока
        Финансовую возможность игрока на удвоение ставки также следует делать вовне

        Аргументы:
            id: int - айди пользователя
        
        Возвращает:
            Player - текущий игрок под айди пользователя
        """
        index = await self.getCurrPlayerInd(id)
        bet = self.players[id][index].bet
        self.players[id][index].bet += bet
        self.players[id][index].money -= bet
        self.players[id][index] = await self.give_cards(id, 1)
        self.players[id][index] = await self.end_move(id)
        return self.players[id][index]

    async def surrender(self, id):
        """
        Метод, соответствующих действию игрока под названием surrender, пользователь сдался

        Команда не проверяет право на surrender согласно правилам blackjack, это делается вовне, команда автоматически завершает ход игрока

        Аргументы:
            id: int - айди пользователя
        
        Возвращает:
            Player - текущий игрок под айди пользователя
        """
        index = await self.getCurrPlayerInd(id)
        self.players[id][index].money += int(self.players[id][index].bet / 2)
        self.players[id][index] = await self.end_move(id, s=True)
        return self.players[id][index]
    
    async def count_dealer(self):
        """
        Метод считает очки дилера и, пока их менее 17-ти, добирает карты

        Возвращает:
            s: int - количество очков дилера
        """
        s = 0
        tuz = []
        for i in self.dealer.hand:
            if points[i] == 11:
                tuz.append(i)
            s += points[i]
            if s > 21 and tuz:
                tuz.pop(0)
                s -= 10
            
        while s < 17:
            self.dealer.hand.append(await self.get_card())
            s = 0
            tuz = []
            for i in self.dealer.hand:
                if points[i] == 11:
                    tuz.append(i)
                s += points[i]
                if s > 21 and tuz:
                    tuz.pop(0)
                    s -= 10
        return s
