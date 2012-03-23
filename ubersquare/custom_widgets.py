# -*- coding: utf-8 -*-

# Copyright (c) 2012 Hugo Osvaldo Barrera <hugo@osvaldobarrera.com.ar>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from PySide.QtGui import QDialog, QVBoxLayout, QLabel
from PySide.QtCore import Signal, SIGNAL, QObject
from PySide.QtMaemo5 import QMaemo5ValueButton, QMaemo5ListPickSelector

class SignalEmittingValueButton(QMaemo5ValueButton):
	def __init__(self, text, callback, parent):
		super(SignalEmittingValueButton, self).__init__(text, parent)
		self.callback = callback

	def setValueText(self, text):
		super(SignalEmittingValueButton, self).setValueText(text)
		self.callback(self.pickSelector().currentIndex())

class WaitingDialog(QDialog):
	def __init__(self, parent = None):
		super(WaitingDialog, self).__init__(parent)
		layout = QVBoxLayout()
		layout.addWidget(QLabel("Please wait; fetching data from foursquare..."))
		self.setLayout(layout)
		self.setWindowTitle("Please wait")


###################### CATEGORY #######################
from PySide.QtCore import *
from PySide.QtGui import *
import foursquare

class CategoryModel(QAbstractListModel):
	def __init__(self, categories):
		super(CategoryModel, self).__init__()
		self.categories = categories

	def rowCount(self, role=Qt.DisplayRole):
		return len(self.categories)

	CategoryRole = 983488936
	SubCategoriesRole = 235246646

	def data(self, index, role=Qt.DisplayRole):
		if role == Qt.DisplayRole:
			return self.categories[index.row()][u'name']
		elif role == Qt.DecorationRole:
			prefix = self.categories[index.row()][u'icon'][u'prefix']
			extension = self.categories[index.row()][u'icon'][u'name']
			return QIcon(foursquare.image(prefix + "64" + extension)) 
		elif role == CategoryModel.CategoryRole:
			return self.categories[index.row()]
		elif role == CategoryModel.SubCategoriesRole:
			return self.categories[index.row()][u'categories']

	def get_data(self, index):
		return self.categories[index]

class CategoryPickSelector(QMaemo5ListPickSelector):
	def __init__(self, categories):
		super(CategoryPickSelector, self).__init__()
		self.setModel(CategoryModel(categories))

class CategorySelector(QWidget):
	def __init__(self, parent = None):
		super(CategorySelector, self).__init__(parent)
		layout = QVBoxLayout()
		self.setLayout(layout)

		self.category = SignalEmittingValueButton("Category", self.category_selected, self)
		self.category.setPickSelector(CategoryPickSelector(foursquare.get_venues_categories()))
		self.category.setValueLayout(QMaemo5ValueButton.ValueBesideText)
		self.subcategory = QMaemo5ValueButton("Subcategory", self)
		self.subcategory.setValueLayout(QMaemo5ValueButton.ValueBesideText)

		layout.addWidget(self.category)
		layout.addWidget(self.subcategory)

	def category_selected(self, index):
		if index != -1:
			subcategories = self.category.pickSelector().model().get_data(index)[u'categories']
			self.subcategory.setPickSelector(CategoryPickSelector(subcategories))

	def selectedCategory(self):
		# There's no pickSelector if a category wasn't even selected
		if self.subcategory.pickSelector():
			index = self.subcategory.pickSelector().currentIndex()
			if index > -1:
				return self.subcategory.pickSelector().model().get_data(index)[u'id']

		index = self.category.pickSelector().currentIndex()
		if index > -1:
			return self.category.pickSelector().model().get_data(index)[u'id']

		return ""

################# WINDOW #########################

class UberSquareWindow(QMainWindow):
	def __init__(self, parent = None):
		super(UberSquareWindow, self).__init__(parent)
		self.setAttribute(Qt.WA_Maemo5StackedWindow)

		showWaitingDialog = Signal()
		self.connect(self, SIGNAL("showWaitingDialog()"), self.__showWaitingDialog)

		hideWaitingDialog = Signal()
		self.connect(self, SIGNAL("hideWaitingDialog()"), self.__hideWaitingDialog)

		networkError = Signal()
		self.connect(self, SIGNAL("networkError()"), self.__networkError)

		self.waitDialog = WaitingDialog(self)

	def __showWaitingDialog(self):
		self.waitDialog.show()

	def __hideWaitingDialog(self):
		self.waitDialog.hide()

	def __networkError(self):
		self.waitDialog.hide()
		d = QMessageBox()
		d.setWindowTitle("Network Error")
		d.setText("I couldn't connect to foursquare to retrieve data. Make sure you're connected to the internet, and try again (keep in mind that it may have been just a network glitch).")
		d.addButton( "Ok", QMessageBox.YesRole)
		d.exec_()