
class Dialog:
	def __init__(self, widgets):
		self.text = widgets
		self.lines = []
		self.cur_line = 0

	def load(self, path):
		self.cur_line = 0
		with open(path, 'r') as f:
			self.lines = f.readlines()

		self._update_text()

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
