from ast import Not
from cgi import test
from math import ceil
from tabnanny import check
from typing import List
from async_timeout import asyncio
from discord import Member, Embed, Intents
from discord.colour import Colour
from discord.ext.commands import AutoShardedBot as Robot
from os import environ
from logging import config, getLogger
from discord.ext.commands.core import guild_only, is_owner

from discord_components import DiscordComponents

from typing import List

from discord import Embed, Message
from discord.abc import Messageable
from discord.member import Member
from discord_components import DiscordComponents, Button, ButtonStyle, Interaction, Select, SelectOption
from asyncio import create_task, sleep, gather
from time import time
from discord.errors import NotFound

ints = Intents(guilds=True, members=True, guild_messages=True, guild_reactions=True)

Token = environ.get("TOKEN3")
Bot = Robot(shard_count=1, command_prefix="=", intents=ints)
DBot = DiscordComponents(Bot)


@Bot.event
async def on_ready():
    print("Bot Started")

def start():
    Bot.run(Token)

from paginator2 import Paginator

@Bot.command()
async def test(ctx):
    embeds = [
        Embed(title="Page1", color=Colour.blue()),
        Embed(title="Page2", color=Colour.red()),
        Embed(title="Page3", color=Colour.purple()),
        Embed(title="Page4", color=Colour.dark_gold()),
        Embed(title="Page5", color=Colour.dark_theme()),
        Embed(title="Page6", color=Colour.green()),
    ]
    j = 0
    for i in embeds:
        i.add_field(name=f"сказка {j}", value="интересная", inline=False)
        j += 1
    
    p = Paginator(DiscordComponents(Bot), ctx.channel.send, embeds, ctx.author.id, values=list(range(6)), forse=1, id=ctx.message.id)
    response = await p.send()
    print(response)


@Bot.command()
async def test2(ctx):
    embeds = [
        Embed(title="Page1", color=Colour.blue()),
        Embed(title="Page2", color=Colour.red()),
        Embed(title="Page3", color=Colour.purple()),
        Embed(title="Page4", color=Colour.dark_gold()),
        Embed(title="Page5", color=Colour.dark_theme()),
        Embed(title="Page6", color=Colour.green()),
    ]
    j = 0
    for i in embeds:
        i.add_field(name=f"история {j}", value="интересная", inline=False)
        j += 1
    
    p = Paginator(DiscordComponents(Bot), ctx.channel.send, embeds, ctx.author.id, values=list(range(6)), forse=1, id=ctx.message.id)
    response = await p.send()
    print(response)


if __name__ == '__main__':
    start()


async def test1():
    for i in range(10):
        print(f"1: {i}")
        await sleep(0.1)
    yield "task 1 is finished"

async def test2():
    for i in range(100):
        print(f"2: {i}")
        await sleep(0.1)
    yield "task 2 is finished"

async def main():
    task1 = asyncio.create_task(test1())
    task2 = asyncio.create_task(test2())
    result = await gather(test1, test2)
    print(result)

#asyncio.run(main())