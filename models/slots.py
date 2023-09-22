"""
Файл с инструментами для работы команды slots
"""

from discord import Colour, Embed
from random import choice

# Номера эмодзи из списка emoji
slots = [1, 2, 3, 4, 5] #0.5, 0.75, 1, 1.25, 1.5 modifier

# Список эмодзи
emoji = ["","🍗", "🍌", "🥥", "🍎", "🍺"]
mod = {
    slots[0] : 0.5, # Коэффициент для эмодзи под номером 1
    slots[1] : 0.75, # Коэффициент для эмодзи под номером 2
    slots[2] : 1, # Коэффициент для эмодзи под номером 3
    slots[3] : 1.25, # Коэффициент для эмодзи под номером 4
    slots[4] : 1.5 # Коэффициент для эмодзи под номером 5
}

# Коэффициенты для комбо
combo = {
    1 : 1, # Совпадение по вертикали 3 в ряд
    2 : 1, # Совпадение по диагонали 3 в ряд
    3 : 2, # Совпадение по горизонтали 5 в ряд
    4 : 1.5, # Совпадение по горизонтали 4 в ряд
    5 : 1 # Совпадение по горизонтали 3 в ряд
}

# Айди эмодзи, сопоставление с элементами списка emoji
emomoji = {
    1 : 811696894149394443,
    2 : 811697988878598144,
    3 : 811698002217271316,
    4 : 811698013696688138,
    5 : 811698023666942034,
    6 : 811698034026479666
}



class Slots(Embed):
    def __init__(self):
        super().__init__(color = Colour.dark_theme())
        # Размер игрального поля
        self.size = (3, 5) #x, y
    
    def randomize(self):
        # Метод заполнения поля случайными номерами эмодзи
        self.roll = [choice(slots) for i in range(self.size[0] * self.size[1])]
    
    def checkwin(self):
        """
        Метод проверки поля на вопрос победы
        Каждая функция check_* возвращает коэффициент, который прибавится к общему коэффициенту и будет умножен на ставку
        
        Возвращает:
            int - общий коэффициент выигрыша
        """
        r = self.roll
        """
        Проверка по вертикали
        x 0 0
        x 0 0
        x 0 0
        """
        def check_vertical(r):
            win = 0
            up = combo[1]
            if r[0] == r[5] == r[10]:
                win += mod[r[0]] * up
            if r[1] == r[6] == r[11]:
                win += mod[r[1]] * up
            if r[2] == r[7] == r[12]:
                win += mod[r[2]] * up
            if r[3] == r[8] == r[13]:
                win += mod[r[3]] * up
            if r[4] == r[9] == r[14]:
                win += mod[r[4]] * up
            return win


        """
        Проверка по диагонали
        x 0 0
        0 x 0
        0 0 x
        """

        def check_bevel(r):
            win = 0
            up = combo[2]
            if r[0] == r[6] == r[12]:
                win += mod[r[0]] * up
            if r[1] == r[7] == r[13]:
                win += mod[r[1]] * up
            if r[2] == r[8] == r[14]:
                win += mod[r[2]] * up
            return win

        
        """
        Проверка по диагонали 2
        0 0 x
        0 x 0
        x 0 0
        """
        
        def check_ubevel(r):
            win = 0
            up = combo[2]
            if r[2] == r[6] == r[10]:
                win += mod[r[2]] * up
            if r[3] == r[7] == r[11]:
                win += mod[r[3]] * up
            if r[4] == r[8] == r[12]:
                win += mod[r[4]] * up
            return win
        
        """
        Проверка на 3, 4 и 5 в ряд
        x x x x x
        0 0 0 0 0
        0 0 0 0 0
        """

        def check_big_line(r):
            win = 0
            up1 = combo[3]
            up2 = combo[4]
            up3 = combo[5]
            if r[0] == r[1] == r[2] == r[3] == r[4]:
                win += up1 * mod[r[0]]
            elif r[0] == r[1] == r[2] == r[3]:
                win += up2 * mod[r[0]]
            elif r[1] == r[2] == r[3] == r[4]:
                win += up2 * mod[r[1]]
            elif r[0] == r[1] == r[2]:
                win += up3 * mod[r[0]]
            elif r[1] == r[2] == r[3]:
                win += up3 * mod[r[1]]
            elif r[2] == r[3] == r[4]:
                win += up3 * mod[r[2]]

            if r[5] == r[6] == r[7] == r[8] == r[9]:
                win += up1 * mod[r[5]]
            elif r[5] == r[6] == r[7] == r[8]:
                win += up2 * mod[r[5]]
            elif r[6] == r[7] == r[8] == r[9]:
                win += up2 * mod[r[6]]
            elif r[5] == r[6] == r[7]:
                win += up3 * mod[r[5]]
            elif r[6] == r[7] == r[8]:
                win += up3 * mod[r[6]]
            elif r[7] == r[8] == r[9]:
                win += up3 * mod[r[7]]

            if r[10] == r[11] == r[12] == r[13] == r[14]:
                win += up1 * mod[r[10]]
            elif r[10] == r[11] == r[12] == r[13]:
                win += up2 * mod[r[10]]
            elif r[11] == r[12] == r[13] == r[14]:
                win += up2 * mod[r[11]]
            elif r[10] == r[11] == r[12]:
                win += up3 * mod[r[10]]
            elif r[11] == r[12] == r[13]:
                win += up3 * mod[r[11]]
            elif r[12] == r[13] == r[14]:
                win += up3 * mod[r[12]]
            return win
        
        # итоговый коэффициент
        win = check_vertical(r) + check_bevel(r) + check_ubevel(r) + check_big_line(r)
        return win

    def spin(self, bet: int):
        """
        Метод, совершающий прокрут и возвращающий итоговый выигрыш и поле с номерами эмодзи

        Аргументы:
            bet: int - ставка пользователя
        
        Возвращает:
            (int, list) - выигрыш, поле
        """
        self.randomize()
        win = self.checkwin()
        return bet * win, self.roll
