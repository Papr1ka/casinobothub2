from handlers import MailHandler
from logging import config, getLogger

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class UserModel():
    __MONEY = 1000
    __EXP = 0
    __LEVEL = 1
    __MESSAGES = 0
    __LEVEL_COST_FORMULA = lambda level: level * (50 + level * 3)
    __CUSTOM = 'игрок'
    __GAMES = 0
    __COLOR = 'dark' #dark or light
    __INVENTORY = []
    __CLAIM = 0
    __FINVENTORY = {
        'rods': [1],
        'ponds': [1],
        'cage': [],
        'components': {}
    }
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
        set start params
        params:
        MONEY: User start money at guild, default=1000
        EXP: User start experience at guild, default=0
        VOICE: User start time at guild voice channels, default=0
        Messages: User start messages at guild text channels, default=0
        LEVEL_FORMULA: level cost function; args=(level)
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
    def exp_to_level(exp, level):
        """
        return user real exp, level
        """
        while exp >= UserModel.__LEVEL_COST_FORMULA(level):
            exp -= UserModel.__LEVEL_COST_FORMULA(level)
            level += 1
        return exp, level, UserModel.__LEVEL_COST_FORMULA(level)
    
    @staticmethod
    def only_exp_to_level(level):
        return UserModel.__LEVEL_COST_FORMULA(level)
