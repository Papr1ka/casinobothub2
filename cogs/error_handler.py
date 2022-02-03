from discord import Embed
from discord.colour import Colour
from discord.errors import Forbidden, NotFound
from discord.ext import commands
from discord.ext.commands.errors import BadArgument, CommandInvokeError, CommandNotFound, CommandOnCooldown, MaxConcurrencyReached, MissingRequiredArgument, MissingPermissions, NoPrivateMessage, NotOwner
import models.errors as errors
from logging import config, getLogger
from handlers import MailHandler
from asyncio import TimeoutError as TError

config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())

class ErrorHandler(commands.Cog):

    __error_embed = Embed(color=Colour.dark_red())
    __delete_after = 3
    
    def __init__(self, Bot):
        self.Bot = Bot
        logger.info(f"{__name__} Cog has initialized")
    
    def getDelay(self):
        return self.__delete_after
    
    """@commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        logger.debug(f'on_command_error(), {error}')
        embed = self.__error_embed
        if isinstance(error, errors.NotEnoughMoney):
            logger.debug('errors.NotEnoughMoney')
            embed.title = error.message
        elif isinstance(error, errors.InvalidUser):
            logger.debug('errors.InvalidUser')
            embed.title = error.message
        elif isinstance(error, errors.CommandCanceled):
            logger.debug('errors.CommandCanceled')
            embed.title = error.message
        elif isinstance(error, MissingRequiredArgument):
            logger.debug('errors.MissingRequiredArgument')
            embed.title = 'Пропущен параметр'
        elif isinstance(error, BadArgument):
            logger.debug('errors.BadArgument')
            embed.title = 'Неверный параметр'
        elif isinstance(error, MissingPermissions):
            logger.debug('errors.MissingPermissions')
            embed.title = 'Недостаточно прав'
        elif isinstance(error, MaxConcurrencyReached):
            logger.debug('errors.MaxConcurrencyReached')
            embed.title = 'Достигнуто максимальное возможное количество вызовов команды'
        elif isinstance(error, NoPrivateMessage):
            logger.debug('errors.NoPrivateMessage')
            embed.title = 'Вызов команды возможен только в контексте гильдии'
        elif isinstance(error, CommandNotFound):
            logger.debug('errors.CommandNotFound')
            embed.title = ""
        elif isinstance(error, BadArgument):
            logger.debug('errors.BadArgument')
            embed.title = 'Неверный параметр'
        elif isinstance(error, CommandOnCooldown):
            embed.title = f'Команда на перезарядке, попробуйте через `{round(error.retry_after, 1)}` секунд'
        elif isinstance(error, Forbidden):
            logger.warning('errors.Forbidden')
            embed.title = ""
        elif isinstance(error, NotFound):
            logger.warning('errors.NotFound')
            embed.title = ""
        elif isinstance(error, CommandInvokeError):
            logger.warning('errors.CommandInvokeError')
            embed.title = ""
        elif isinstance(error, TError):
            embed.title = ""
        elif isinstance(error, TimeoutError):
            embed.title = ""
        elif isinstance(error, NotOwner):
            embed.title = ""
        else:
            logger.error(error)
            embed.title = 'Что-то пошло не так'
        if embed.title != "":
            await ctx.send(embed=embed, delete_after=self.__delete_after)"""

    @staticmethod
    async def on_error(channel, error):
        embed = Embed(color=Colour.dark_teal())
        if isinstance(error, errors.NotSelectedBetType):
            logger.debug('errors.NotSelectedBetType')
        elif isinstance(error, errors.BadGamesession):
            logger.debug('errors.BadGamesession')
        elif isinstance(error, errors.NotEnoughMoney):
            logger.debug('errors.NotEnoughMoney')
        elif isinstance(error, errors.TooManyGames):
            logger.debug('errors.TooManyGames')
        embed.title = error.message
        await channel.send(embed=embed, delete_after=ErrorHandler.__delete_after)
            
            

def setup(Bot):
    Bot.add_cog(ErrorHandler(Bot))
