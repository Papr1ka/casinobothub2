from discord.ext.commands import Cog
from discord import ChannelType, Message
from asyncio import sleep
from logging import config, getLogger

from database import db
from models.to_update import To_update
from handlers import MailHandler
from discord import ChannelType, Message


config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class Leveling(Cog):

    leveling_table = {
        'message': 10,
        'fishing': 10,
        'casino': 20
    }
    timing = 60

    @Cog.listener()
    async def on_message(self, message: Message):
        if not message.author.bot and not message.is_system() and message.channel.type is ChannelType.text:
            user = (message.guild.id, message.author.id)
            self.queue.add(user)
    
    
    async def update_users(self):
        while True:
            await sleep(self.timing)
            q = self.queue.get()
            await db.update_many([
                [i[0], i[1], {'$inc': {'exp': self.leveling_table['message'] * q[i], 'messages': q[i]}}] for i in q
            ])



    def __init__(self, Bot):
        self.Bot = Bot
        self.Bot.loop.create_task(self.update_users())
        self.queue = To_update()
        logger.info(f"{__name__} Cog has initialized")



def setup(Bot):
    Bot.add_cog(Leveling(Bot))
    
LevelTable = Leveling.leveling_table