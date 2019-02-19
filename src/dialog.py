
class Dialog:
	def __init__(self, textboxes, info):
		self.text = textboxes
		self.info = info
		self._reset()

	def _reset(self):
		self.lines = []
		self.characters = []
		self.unique = 0 # Num unique characters.
		self.cur_line = 0

	def load(self, path):
		self._reset()
		chars = set()
		with open(path, 'r') as f:
			for l in f:
				char_line = l.split(' ', 1)
				c_id = int(char_line[0])
				self.characters.append(c_id)
				self.lines.append(char_line[1])
				if c_id not in chars:
					chars.add(c_id)
					self.unique += 1

		self._update_text()
		self._update_info()

	def prev(self):
		self.goto(self.cur_line - 1)

	def next(self):
		self.goto(self.cur_line + 1)

	def goto(self, line):
		self.cur_line = max(0, min(line, len(self.lines)-1))
		self._update_text()

	def _update_text(self):
		for i, text in enumerate(self.text):
			line = i + self.cur_line - 1
			text.config(state='normal')
			text.delete(1.0, 'end')
			if line >= 0 and line < len(self.lines):
				text.insert('end', self.lines[line])
			text.config(state='disabled')

	def _update_info(self):
		l = len(self.lines)
		self.info.config(text=f'Lines: 0/{l}\nChars: 0/{self.unique}')