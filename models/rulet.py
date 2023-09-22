"""
Файл с инструментами для работы команды rulet
"""

from handlers import MailHandler
from random import choice
from logging import config, getLogger

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class Rulet():
	"""
	Класс рулетки
	"""

	# Разметка значений колеса рулетки
	# Номер: (цвет, чётность, дюжина)
	__fields = {
		#color | % 2 | line
		1 : ("red", "odd", 1),
		2 : ('black', 'even', 2),
		3 : ('red', 'odd', 3),
		4 : ('black', 'even', 1),
		5 : ('red', 'odd', 2),
		6 : ('black', 'even', 3),
		7 : ('red', 'odd', 1),
		8 : ('black', 'even', 2),
		9 : ('red', 'odd', 3),
		10 : ('black', 'even', 1),
		11 : ('black', 'odd', 2),
		12 : ('red', 'even', 3),
		13 : ('black', 'odd', 1),
		14 : ('red', 'even', 2),
		15 : ('black', 'odd', 3),
		16 : ('red', 'even', 1),
		17 : ('black', 'odd', 2),
		18 : ('red', 'even', 3),
		19 : ('red', 'odd', 1),
		20 : ('black', 'even', 2),
		21 : ('red', 'odd', 3),
		22 : ('black', 'even', 1),
		23 : ('red', 'odd', 2),
		24 : ('black', 'even', 3),
		25 : ('red', 'odd', 1),
		26 : ('black', 'even', 2),
		27 : ('red', 'odd', 3),
		28 : ('black', 'even', 1),
		29 : ('black', 'odd', 2),
		30 : ('red', 'even', 3),
		31 : ('black', 'odd', 1),
		32 : ('red', 'even', 2),
		33 : ('black', 'odd', 3),
		34 : ('red', 'even', 1),
		35 : ('black', 'odd', 2),
		36 : ('red', 'even', 3),
		0 : ('null', 'null', 'null')
	}
	
	# Разметка поля рулетки
	__field = (0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26)
	# Длина поля
	__field_len = __field.__len__()
	
	# Шаг прокрутки, шаг виден при обновлении Embed сообщения рулетки
	__step = 9
	# Коэффициенты выигрыша
	__koofs = {
		'color': 2, # Ставка на цвет, 1 к 1
		'parity': 2, # Ставка на чётность, 1 к 1
		'line': 3, # Ставка на линию, 1 к 2
		'group': 3, # Ставка на дюжину, 1 к 2
		'number': 36 # Ставка на число, 1 к 35
	}

	def __init__(self, step: int = 9):
		if step > self.__field_len:
			self.step = self.__step
		else:
			self.step = step
		logger.debug("Rulet initialized")
	
	def check(self, number: int):
		"""
		Метод, возвращающий описание поля

		Аргументы:
			number: int - номер поля
		
		Возвращает:
			Tuple(color: str, parity: str, group: int)
		"""
		return self.__fields[number]

	def spin(self, rolls: int=5):
		"""
		Метод, является генератором
		При вызове next() или в цикле, на каждой итерации возвращает отрезок поля

		Аргументы:
			rolls: int - Количество прокрутов
		
		Возвращает на итерации:
			fields: Tuple[int] - кортеж с номерами полей длины __step
		"""
		# Стартовая позиция
		start_pos = self.__field.index(choice(self.__field))
		for i in range(rolls):
			# Если отрезок выходит за рамки поля
			if start_pos + self.step > self.__field_len:
				yield self.__field[start_pos:self.__field_len] + self.__field[0: self.step - self.__field_len + start_pos]
				start_pos = (start_pos + self.step) % self.__field_len
			# Если не выходит за рамки поля
			else:
				yield self.__field[start_pos:start_pos + self.step]
				start_pos += self.step
