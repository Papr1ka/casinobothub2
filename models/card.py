"""
Файл содержит инструментарий для работы команды status
"""

from aiohttp import ClientSession as aioSession
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw


class Card():
    """
    Класс для отрисовки карточки пользователя
    """

    # размер карточки в пикселях
    __size = (980, 320)
    # первый шрифт, используется для отрисовки имени, роли и описания пользователя
    __main_font = ImageFont.truetype('media/Montserrat.ttf', 32)
    # второй шрифт, используется для отрисовки количества опыта пользователя
    __second_font = ImageFont.truetype('media/Montserrat.ttf', 28)
    # третий шрифт, используется для отрисовки уровня пользователя
    __third_font = ImageFont.truetype('media/Montserrat.ttf', 40)
    # отступы от края в пикселях
    __padding = (35, 35)
    # размер аватара в пикселях
    __avatar_size = (250, 250)
    # цвет заполнения полоски уровня в rgb
    __bar_color = (98, 211, 245)

    def __init__(self, user_data: dict):
        """
        Функция инициализации, создаёт объекты изображения, рисования, инициализирует переменны

        Аргументы:
            user_data: Dict[str, Any] - словарь с данными о пользователе
            используются значения по следующим ключам:
                _id: int - айди пользователя для создания файла с уникальным именем
                color: str - цвет темы (dark | light)
                avatar: str - ссылка на аватар пользователя
                username: str - имя пользователя
                exp: int - опыт пользователя
                level: int - уровень пользователя
                exp_to_next_level: int - опыт, необходимый для повышения уровня пользователя
        """
        self.data = user_data
        # цвет заднего фона
        self.__bg_color = (8, 8, 8) if self.data['color'] == 'dark' else (240, 240, 240)
        # цвет текста
        self.__text_color = (255, 255, 255, 192) if self.data['color'] == 'dark' else (8, 8, 8, 256)
        # объект изображения
        self.img = Image.new('RGBA', self.__size, self.__bg_color)
        # объект ImageDraw
        self.draw = ImageDraw.Draw(self.img)
        # относительное имя файла
        self.filename = f"media/{self.data['_id']}.png"

    async def __remove_transparency(self, im: Image):
        """
        Метод заменяет прозрачность изображения на цвет фона (__bg_color)
        
        Аргументы:
            im: Image - объект изображения
        
        Возвращает:
            bg: Image - обработанное изображение
        """
        alpha = im.convert('RGBA').split()[-1]
        bg = Image.new("RGBA", im.size, self.__bg_color)
        bg.paste(im, mask=alpha)
        return bg

    async def __add_corners(self, im: Image, rad: int=120):
        """
        Метод добавления закруглений изображению по углам
        Используется для округления аватара и карточки

        Аргументы:
            im: Image - объект изображения
            rad: int - радиус закругления, 125 - идеальный круг, максимум, 0 - квадрат без закруглений
        
        Возвращает:
            im: Image - обработанное изображение

        """
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
        """
        Метод получения скачивает аватар из интернета,
        закругляет, удаляет прозрачность и вставляет на место в карточке
        """

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
        """
        Метод отрисовки текстовой информации о пользователе
        """
        # Отрисовка имени пользователя
        username = self.data['username'][:14]
        self.draw.text((320, 180), username, font=self.__main_font, fill=self.__text_color)

        # Отрисовка прогрес бара
        exp, level, exp_to_level = self.data['exp'], self.data['level'], self.data['exp_to_next_level']

        await self.__render_progress_bar(int((exp / exp_to_level) * 100))

        # Отрисовка количества опыта
        postfix = ' XP'
        if exp_to_level > 1000:
            postfix = ' K XP'
            pattern = '{:.2f}'
            exp, exp_to_level = pattern.format(exp / 1000), pattern.format(exp_to_level / 1000)

        level_line = f'{exp} / {exp_to_level}{postfix}'
        self.draw.text((930, 219), level_line, font=self.__second_font, fill=(18, 188, 199, 256), anchor='rd')
        # Отрисовка уровня
        self.draw.text((930, self.__padding[1]), 'LVL ' + str(level), font=self.__third_font, fill=(18, 188, 199, 192), anchor='ra')
        # Отрисовка роли
        self.draw.text((320, self.__padding[1]), '@' + self.data['top_role'], font=self.__main_font, fill=self.data['role_color'])
        # Отрисовка описания пользователя (статуса)
        self.draw.text((320, self.__padding[1] + 40), '#' + self.data['custom'], font=self.__main_font, fill=(120, 120, 120))
    
    async def __render_progress_bar(self, prcnts: int):
        """
        Метод отрисовки прогрес база

        Аргументы:
            prcnts: int - процент заполненности
        """

        # Для отрисовки используются уже готовые изображения из папки media, progress.png для тёмной темы и progress2.png для светлой
        bname = 'media/'
        if self.data['color'] == 'dark':
            bname += 'progress.png'
        elif self.data['color'] == 'light':
            bname += 'progress2.png'
        bar = Image.open(bname).convert('RGB')
        draw = ImageDraw.Draw(bar)

        # Сколько пикселей заполнить
        to_fill = 612 / 100 * prcnts
        if to_fill >= 595:
            # Середина последнего круга диаметром 34, который можно нарисовать
            x, y, diam = 595, 8, 34
        elif to_fill >= 17:
            # Относительные координаты согласно процентам
            x, y, diam = to_fill - 4, 8, 34
        else:
            # Прогрес бар следует сделать пустым
            # Вставка прогрес бара в общуй карточку
            self.img.paste(bar, (306, 220))
            return
        # Отрисовка крайнего правого круга
        draw.ellipse((x, y, x + diam, y + diam), fill=self.__bar_color)
        # Заполнение области прогресс бара до круга
        ImageDraw.floodfill(bar, xy=(14, 25), value=self.__bar_color, thresh=40)
        # Вставка прогрес бара в общуй карточку
        self.img.paste(bar, (306, 220))

    async def save(self):
        """
        Метод сохранения текущего изображения

        Возвращает:
            filename: str - относительный путь сохранённого файла
        """
        self.img.save(self.filename)
        return self.filename

    async def render_get(self):
        """
        Метод создания карточки
        
        Возвращает:
            filename: str - относительный путь созданного файла
        """
        self.img = await self.__add_corners(self.img, 10)
        await self.__render_avatar()
        await self.__render_info()
        return await self.save()
