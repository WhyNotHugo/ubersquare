from PySide.QtMaemo5 import QMaemo5ValueButton

class SignalEmittingValueButton(QMaemo5ValueButton):
	def __init__(self, text, callback, parent):
		super(SignalEmittingValueButton, self).__init__(text, parent)
		self.callback = callback

	def setValueText(self, text):
		super(SignalEmittingValueButton, self).setValueText(text)
		self.callback(self.pickSelector().currentIndex())