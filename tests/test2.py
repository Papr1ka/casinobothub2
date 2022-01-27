from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageChops
from io import BytesIO
from requests import get
import os
import asyncio

from models.user_model import UserModel

import aiohttp
from aiofiles import open

level_cost = 1000

def calculate_level(exp : int):
    level = exp // level_cost
    exp_on_level = exp - level * level_cost
    return level, exp_on_level, level_cost


class Card():
    __size = (980, 320)
    __main_font = ImageFont.truetype('Montserrat.ttf', 32)
    __second_font = ImageFont.truetype('Montserrat.ttf', 28)
    __third_font = ImageFont.truetype('Montserrat.ttf', 40)
    __padding = (35, 35)
    __avatar_size = (250, 250)
    __linear_size = 1
    __bg_color = (8, 8, 8)

    def __init__(self, user_data):
        self.data = user_data
        self.img = Image.new('RGBA', self.__size, self.__bg_color)
        self.draw = ImageDraw.Draw(self.img)
        self.filename = f"{self.data['_id']}.png"
        self.color = self.data['role_color']

    async def remove_transparency(self, im):
        alpha = im.convert('RGBA').split()[-1]
        bg = Image.new("RGBA", im.size, self.__bg_color + (255,))
        bg.paste(im, mask=alpha)
        return bg

    async def add_corners(self, im, rad=120):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, "white")
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        alpha = ImageChops.darker(alpha, im.split()[-1])
        im.putalpha(alpha)
        return im
    
    async def render_avatar(self):

        async with aiohttp.ClientSession() as session:
            async with session.get(self.data['avatar']) as resp:
                if resp.status == 200:
                    r = await resp.read()
                    r = Image.open(BytesIO(r))
                    r.convert('RGBA')
                    r.resize(self.__avatar_size)
        
        pl = await self.add_corners(r)
        pl = await self.remove_transparency(pl)
        self.img.paste(pl, self.__padding)
    

    async def render_info(self):
        username = self.data['username'][:14] + '#' + self.data['discriminator']
        self.draw.text((320, 180), username, font=self.__main_font, fill=(255, 255, 255, 192))

        exp, level, exp_to_level = UserModel.exp_to_level(self.data['exp'], self.data['level'])

        await self.render_progress_bar(int((exp / exp_to_level) * 100))

        postfix = ' XP'
        if exp_to_level > 1000:
            postfix = ' K XP'
            pattern = '{:.2f}'
            exp, exp_to_level = pattern.format(exp / 1000), pattern.format(exp_to_level / 1000)
        level_line = f'{exp} / {exp_to_level}{postfix}'
        self.draw.text((930, 219), level_line, font=self.__second_font, fill=(18, 188, 199, 256), anchor='rd')
        self.draw.text((930, self.__padding[1]), 'LVL ' + str(level), font=self.__third_font, fill=(18, 188, 199, 192), anchor='ra')
        self.draw.text((320, self.__padding[1]), '@' + self.data['top_role'], font=self.__main_font, fill=self.data['role_color'])
        self.draw.text((320, self.__padding[1] + 40), '#' + self.data['custom'], font=self.__main_font, fill=(120, 120, 120))
    
    async def render_progress_bar(self, prcnts):
        print(prcnts)
        bar = Image.open('progress.png').convert('RGB')
        draw = ImageDraw.Draw(bar)
        color = (98,211,245)
        to_fill = 612 / 100 * prcnts
        print(to_fill)
        if to_fill >= 595:
            x, y, diam = 595, 8, 34
        elif to_fill >= 17:
            x, y, diam = to_fill - 4, 8, 34
        else:
            self.img.paste(bar, (306, 220))
            return
        draw.ellipse((x, y, x + diam, y + diam), fill=color)
        ImageDraw.floodfill(bar, xy=(14, 25), value=color, thresh=40)
        self.img.paste(bar, (306, 220))




    async def save(self):
        self.img = await self.add_corners(self.img, 10)
        self.img.save(self.filename)
        self.img.show()


async def main():
    c = Card({
        '_id': 1234,
        'role_color': (256, 256, 256),
        'avatar': 'https://cdn.discordapp.com/avatars/397352286487052288/503e1f8c57ea6cdb3fefb8ed6d695059.webp?size=1024',
        'username': 'Papr1kaPapr1kaPapr1ka',
        'discriminator': '8145',
        'exp': 1000000,
        'level': 3,
        'custom': 'игрок',
        'top_role': 'Матрос',
        'role_color': (0, 255, 0)
        })
    await c.render_avatar()
    await c.render_info()
    await c.save()


if __name__ == "__main__":
    asyncio.run(main())