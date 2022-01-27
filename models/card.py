from aiohttp import ClientSession as aioSession
from io import BytesIO
from models.user_model import UserModel
from PIL import Image, ImageFont, ImageDraw


class Card():
    __size = (980, 320)
    __main_font = ImageFont.truetype('media/Montserrat.ttf', 32)
    __second_font = ImageFont.truetype('media/Montserrat.ttf', 28)
    __third_font = ImageFont.truetype('media/Montserrat.ttf', 40)
    __padding = (35, 35)
    __avatar_size = (250, 250)
    __bar_color = (98,211,245)

    def __init__(self, user_data):
        self.data = user_data
        self.__bg_color = (8, 8, 8) if self.data['color'] == 'dark' else (240, 240, 240)
        self.__text_color = (255, 255, 255, 192) if self.data['color'] == 'dark' else (8, 8, 8, 256)
        self.img = Image.new('RGBA', self.__size, self.__bg_color)
        self.draw = ImageDraw.Draw(self.img)
        self.filename = f"media/{self.data['_id']}.png"

    async def __remove_transparency(self, im):
        alpha = im.convert('RGBA').split()[-1]
        bg = Image.new("RGBA", im.size, self.__bg_color)
        bg.paste(im, mask=alpha)
        return bg

    async def __add_corners(self, im, rad=120):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, "white")
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im
    
    async def __render_avatar(self):

        async with aioSession() as session:
            async with session.get(self.data['avatar']) as resp:
                if resp.status == 200:
                    r = await resp.read()
                    r = Image.open(BytesIO(r))
                    r.convert('RGBA')
                    r.resize(self.__avatar_size)
        im = await self.__add_corners(r)
        im = await self.__remove_transparency(im)
        self.img.paste(im, self.__padding)
    
    async def __render_info(self):
        username = self.data['username'][:14] + '#' + self.data['discriminator']
        self.draw.text((320, 180), username, font=self.__main_font, fill=self.__text_color)

        exp, level, exp_to_level = UserModel.exp_to_level(self.data['exp'], self.data['level'])

        await self.__render_progress_bar(int((exp / exp_to_level) * 100))

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
    
    async def __render_progress_bar(self, prcnts):
        bname = 'media/'
        if self.data['color'] == 'dark':
            bname += 'progress.png'
        elif self.data['color'] == 'light':
            bname += 'progress2.png'
        bar = Image.open(bname).convert('RGB')
        draw = ImageDraw.Draw(bar)
        to_fill = 612 / 100 * prcnts
        if to_fill >= 595:
            x, y, diam = 595, 8, 34
        elif to_fill >= 17:
            x, y, diam = to_fill - 4, 8, 34
        else:
            self.img.paste(bar, (306, 220))
            return
        draw.ellipse((x, y, x + diam, y + diam), fill=self.__bar_color)
        ImageDraw.floodfill(bar, xy=(14, 25), value=self.__bar_color, thresh=40)
        self.img.paste(bar, (306, 220))

    async def save(self):
        self.img.save(self.filename)
        return self.filename

    async def render_get(self):
        self.img = await self.__add_corners(self.img, 10)
        await self.__render_avatar()
        await self.__render_info()
        return await self.save()
