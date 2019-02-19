
class Dialog:
	def __init__(self, textboxes, info):
		self.text = textboxes
		self.info = info
		self.lines = []
		self.cur_line = 0
		self.characters = set()

	def load(self, path):
		self.lines = []
		self.cur_line = 0
		self.characters = set()
		with open(path, 'r') as f:
			for l in f:
				char_line = l.split(' ', 1)
				self.characters.add(int(char_line[0]))
				self.lines.append(char_line[1])

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
		c = self.characters.__len__()
		self.info.config(text=f'Lines: 0/{l}\nChars: 0/{c}')