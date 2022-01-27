from handlers import MailHandler
from random import choice
from logging import config, getLogger

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class Rulet():
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
	__field = (0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26)
	__field_len = __field.__len__()
	__step = 9
	__koofs = {
		'color': 2, #1 to 1
		'parity': 2, #1 to 1
		'line': 3, #1 to 2
		'group': 3, #1 to 2
		'number': 36 #1 to 35
	}

	def __init__(self, step: int = 9):
		if step > self.__field_len:
			self.step = self.__step
		else:
			self.step = step
		logger.debug("Rulet initialized")
	
	def check(self, number: int):
		return self.__fields[number]

	def spin(self, rolls=5):
		start_pos = self.__field.index(choice(self.__field))
		for i in range(rolls):
			if start_pos + self.step > self.__field_len:
				yield self.__field[start_pos:self.__field_len] + self.__field[0: self.step - self.__field_len + start_pos]
				start_pos = (start_pos + self.step) % self.__field_len
			else:
				yield self.__field[start_pos:start_pos + self.step]
				start_pos += self.step
