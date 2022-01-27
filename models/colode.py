from random import choice

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
    def __init__(self, name, bet, money, id) -> None:
        self.name = name
        self.bet = bet
        self.split = False
        self.cards = 9999999999
        self.money = money
        self.end = False
        self.hand = []
        self.id = id
        self.surrender = False
    
    def __str__(self) -> str:
        return f"name: {self.name}; bet: {self.bet}; split: {self.split}; cards: {self.cards}; money: {self.money}; end: {self.end}; hand: {self.hand}; surrender: {self.surrender}"

    def __repr__(self) -> str:
        return self.__str__()
    
    def from_dict(self, inf):
        a = Player(inf['name'], inf['bet'], inf['money'], inf['id'])
        a.split = inf['split']
        a.cards = inf['cards']
        a.end = inf['end']
        a.hand = inf['hand']
        a.id = inf['id']
        a.surrender = inf['surrender']
        return a
    
    def sm(self):
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
    
    def __init__(self, bet) -> None:
        self.players = {}
        self.played = {}
        self.reg = []
        self.bet = bet
        self.colode = col.copy()
        self.dealer: Player
    
    async def add_player(self, id, name, money):
        self.players[id] = [Player(name, self.bet, money, id)]
        self.played[id] = [1]
        self.reg.append(id)
    
    async def get_card(self):
        card = choice(self.colode)
        self.colode.remove(card)
        return card
    
    async def give_cards(self, player_id, amount):
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
        for i in range(len(self.players[id])):
            if self.players[id][i].end is False:
                return i
        return None
    
    async def create_dealer(self):
        self.dealer = Player(
            "👤 Дилер",
            self.bet,
            99999999999999,
            None
        )
        self.dealer.hand.append(await self.get_card())
        self.dealer.hand.append(await self.get_card())
        
    async def change(self, id, index, **arg):
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
        
    async def end_move(self, id, s=False):
        index = await self.getCurrPlayerInd(id)
        self.played[id][index] -= 1
        await self.change(id, index, end=True, surrender=s)
        return self.players[id][index]
    
    async def split(self, id):
        index = await self.getCurrPlayerInd(id)
        player = self.players[id][index]
        player.split = True
        self.players[id] = [player, player]
        self.played[id] = [1, 1]
        hand1 = [player.hand[0], await self.get_card()]
        hand2 = [player.hand[1], await self.get_card()]
        await self.change(id, 0, hand=hand1)
        await self.change(id, 1, hand=hand2)
        return self.players[id]

    async def double(self, id):
        index = await self.getCurrPlayerInd(id)
        bet = self.players[id][index].bet
        self.players[id][index].bet += bet
        self.players[id][index].money -= bet
        self.players[id][index] = await self.give_cards(id, 1)
        self.players[id][index] = await self.end_move(id)
        return self.players[id][index]

    async def surrender(self, id):
        index = await self.getCurrPlayerInd(id)
        self.players[id][index].money += int(self.players[id][index].bet / 2)
        self.players[id][index] = await self.end_move(id, s=True)
        return self.players[id][index]
    
    async def count_dealer(self):
        
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
