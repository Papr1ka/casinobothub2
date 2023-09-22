"""
Файл, описывающий класс для создания пользователя и пересчёта чистого опыта в уровни
"""

from handlers import MailHandler
from logging import config, getLogger

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class UserModel():
    """
    Класс модели пользователя, используется для создании записи в базе данных о новом пользователе
    """
    # Поля по умолчанию
    # Деньги
    __MONEY = 1000
    # Опыт
    __EXP = 0
    # Уровень
    __LEVEL = 1
    # Сообщения
    __MESSAGES = 0
    # Функция получения количества опыта, необходимого для повышения уровня
    __LEVEL_COST_FORMULA = lambda level: level * (50 + level * 3)
    # Описание в карточке (status) по умолчанию
    __CUSTOM = 'игрок'
    # Количество игр в казино
    __GAMES = 0
    # Значение темы по умолчанию (dark | light)
    __COLOR = 'dark'
    # Список неактивированных предметов из магазина
    __INVENTORY = []
    # Последнее время получения награды за голосование
    __CLAIM = 0
    # Инвентарь рыбака
    __FINVENTORY = {
        # Удочки, которые есть у пользователя
        'rods': [1],
        # Водоёмы, которые приобрёл пользователь
        'ponds': [1],
        # Рыба в садке
        'cage': [],
        # Компоненты для создания удочек
        'components': {}
    }
    # Приобретённые виды бизнеса у пользователя
    __BUSINESS = []
    __slots__ = ['__user_id', '__money', '__exp', '__messages', '__level', '__custom', '__color', '__games', '__inventory', '__claim', '__finventory', '__business', '__guild_id']
    slots = [i[2:] for i in __slots__]

    def __init__(self, user_id, guild_id):
        self.__user_id = user_id
        self.__guild_id = guild_id
        self.__money = self.__MONEY
        self.__messages = self.__MESSAGES
        self.__custom = self.__CUSTOM
        self.__color = self.__COLOR
        self.__games = self.__GAMES
        self.__inventory = self.__INVENTORY
        self.__exp, self.__level, _ = self.exp_to_level(self.__EXP, self.__LEVEL)
        self.__claim = self.__CLAIM
        self.__finventory = self.__FINVENTORY
        self.__business = self.__BUSINESS
        logger.debug('created UserModel')
    
    def get_custom():
        return UserModel.__CUSTOM
    
    @classmethod
    def set_cls_field(cls, **params):
        """
        Изменение значений по умолчанию, которые будут использованы при создании нового пользователя

        Метод изменит значения до завершения программы, на данный момент нигде не используется

        Аргументы:
            params: dict - Словарь, где ключ - название поля по умолчанию, значение - значение по умолчанию
        """
        logger.info(f'new UserModel start params: {params}')
        cls.__MONEY = params.pop('MONEY', 1000)
        cls.__EXP = params.pop('EXP', 0)
        cls.__MESSAGES = params.pop('MESSAGES', 0)
        cls.__CUSTOM = params.pop('CUSTOM', 'игрок')
        cls.__COLOR = params.pop('COLOR', 'dark')
        cls.__GAMES = params.pop('GAMES', 0)
        cls.__INVENTORY = params.pop('INVENTORY', 0)
        cls.__CLAIM = params.pop("CLAIM", 0)
        cls.__FINVENTORY = params.pop("FINVENTORY", {
        'rods': [],
        'ponds': [],
        'cage': [],
        'components': {}
    })
        cls.__BUSINESS = params.pop("BUSINESS", [])
        cls.__LEVEL_COST_FORMULA = params.pop('LEVEL_COST_FORMULA', lambda level: level * (50 + level * 3))
    
    def get_json(self):
        """
        Метод для получения информации о пользователе в формате json
        """
        return {
            '_id': self.__user_id,
            'guild_id': self.__guild_id,
            'money': self.__money,
            'exp': self.__exp,
            'level': self.__level,
            'games': self.__games,
            'messages': self.__messages,
            'custom': self.__custom,
            'inventory': self.__inventory,
            'color': self.__color,
            'claim': self.__claim,
            'finventory': self.__finventory,
            'business': self.__business
        }
    
    @staticmethod
    def exp_to_level(exp: int, level: int):
        """
        Метод для перевода опыта и текущего уровня пользователя
        в максимально возможный уровень для текущего опыта и остаточный опыт
        
        Аргументы:
            exp: int - текущий опыт пользователя
            level: int - текущий уровень пользователя

        Возвращает:
            (exp: int, level: int, exp_to_next_level: int)
            exp - остаточное количество опыта
            level - новый уровень пользователя
            ext_to_next_level - количество опыта, необходимое для перехода на следующий уровень
            (абсолютная величина (см. комментарий к only_exp_tp_level))
        """
        while exp >= UserModel.__LEVEL_COST_FORMULA(level):
            exp -= UserModel.__LEVEL_COST_FORMULA(level)
            level += 1
        return exp, level, UserModel.__LEVEL_COST_FORMULA(level)
    
    @staticmethod
    def only_exp_to_level(level: int):
        """
        Метод для получения количества опыта, необходимого для перехода на следующий уровень
        (Абсолютная величина перехода)
        Чтобы получить отностельную, нужно дополнительно
        вне функции отнять от результата работы этой функции текущее количество опыта пользователя

        Аргументы:
            level: int - текущий уровень пользователя

        Возвращает:
            exp_to_next_level: int - количество опыта, необходимого для перехода на следуюший уровень
        """
        return UserModel.__LEVEL_COST_FORMULA(level)
