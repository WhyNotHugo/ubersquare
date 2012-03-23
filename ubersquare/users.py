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

from PySide.QtGui import QListView, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QIcon, QScrollArea, QGridLayout, QLabel, QImage, QPixmap, QPushButton
from PySide.QtCore import QAbstractListModel, Qt, Signal, SIGNAL
import foursquare
from foursquare import Cache
import ubersquare.gui

class UserProfile(QWidget):
	def __init__(self, user, parent = None):
		super(UserProfile, self).__init__(parent)

		name = user[u'user'][u'firstName']
		if u'lastName' in user[u'user']:
			name += " " + user[u'user'][u'lastName']

		description = "<b>" + name + "</b>"
		if u'homeCity' in user[u'user']:
			description += "<br>from " + user[u'user'][u'homeCity']
		if u'scores' in user:
			description += "<br>Score: "
			if u'recent' in user[u'scores']:
				description += str(user[u'scores'][u'recent'])
			if u'max' in user[u'scores']:
				description += " (" + str(user[u'scores'][u'max']) + " max)"

		self.descriptionLabel = QLabel()
		self.descriptionLabel.setText(description)
		self.descriptionLabel.setWordWrap(True)

		self.photo_label = QLabel()
		self.photo = QImage(foursquare.image(user[u'user'][u'photo']))
		self.photo_label.setPixmap(QPixmap(self.photo))

		profileLayout = QGridLayout()
		self.setLayout(profileLayout)
		profileLayout.addWidget(self.photo_label, 0, 0)
		profileLayout.addWidget(self.descriptionLabel, 0, 1, 1, 2)

		#profileLayout.addWidget(QLabel("current user location"), 1, 0, 1, 3)

class UserDetailsWindow(QMainWindow):
	def __init__(self, user, fullDetails, parent):
		super(UserDetailsWindow, self).__init__(parent)
		self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.user = user
		self.fullDetails = fullDetails

		self.centralWidget = QWidget() 
		self.setCentralWidget(self.centralWidget) 

		layout = QVBoxLayout() 
		layout.setSpacing(0)         
		self.centralWidget.setLayout(layout) 

		self.container = QWidget()
		self.scrollArea = QScrollArea() 
		self.scrollArea.setWidget(self.container)
		self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

		layout.addWidget(self.scrollArea)
		self.scrollArea.setWidgetResizable(True)

		gridLayout = QGridLayout() 
		self.container.setLayout(gridLayout) 

		firstName = user[u'user'][u'firstName']
		name = firstName
		if u'lastName' in user[u'user']:
			name += " " + user[u'user'][u'lastName']
		self.setWindowTitle(name)

		photo_label = QLabel()
		photo = QImage(foursquare.image(self.user[u'user'][u'photo']))
		photo_label.setPixmap(QPixmap(photo))

		i = 0
		gridLayout.addWidget(UserProfile(user), i, 0, 2, 1)
		gridLayout.addWidget(QPushButton("More info"), i, 1, 1, 1)
		i += 1
		# ONLY IF FRIEND!!
		gridLayout.addWidget(QPushButton("Unfriend"), i, 1, 1, 1)
		fullDetails = True # TODO: debug stuff!!
		if user[u'user'][u'id'] == "17270875":
			i += 1
			gridLayout.addWidget(QLabel("<b>This is the UberSquare developer!</b>"), i, 0, 1, 2)

		if not fullDetails:
			i += 1
			gridLayout.setRowStretch(i, 5)
		else:
			i += 1
			gridLayout.addWidget(QLabel("X Mayorships"), i, 0)
			i += 1
			gridLayout.addWidget(QLabel("Y Badges"), i, 0)
			i += 1
			gridLayout.addWidget(QPushButton("See places " + firstName + " has been to."), i, 0, 1, 2)
			i += 1
			gridLayout.addWidget(QPushButton("Say no to drugs!!!"), i, 0, 1, 2)
			i += 1
			gridLayout.addWidget(QPushButton("Say no to drugs!!!"), i, 0, 1, 2)
			i += 1
			gridLayout.addWidget(QPushButton("Say no to drugs!!!"), i, 0, 1, 2)
			i += 1
			gridLayout.addWidget(QPushButton("Say no to drugs!!!"), i, 0, 1, 2)

class UserListModel(QAbstractListModel):
	def __init__(self, users):
		super(UserListModel, self).__init__()
		self.users = users

	UserRole = 54514533

	def rowCount(self, role=Qt.DisplayRole):
		if self.users:
			return len(self.users)
		else:
			return 0

	def data(self, index, role=Qt.DisplayRole):
		user = self.users[index.row()][u'user']
		if role == Qt.DisplayRole:
			text = user[u'firstName']
			if u'lastName' in user:
				text += " " + user[u'lastName']
			score = self.users[index.row()][u'scores']
			text += "\n  " + str(score[u'recent']) + "/" + str(score[u'max']) + " (" + str(score[u'checkinsCount']) + " checkins" + ")"
			return text
		elif role == Qt.DecorationRole:
			return QIcon(foursquare.image(user[u'photo']))
		elif role == UserListModel.UserRole:
			return self.users[index.row()]

	def setUsers(self, users):
		self.users = users
		self.reset()

class UserList(QListView):
	def __init__(self, users, parent):
		super(UserList,self).__init__(parent)
		self.model = UserListModel(users)
		self.setModel(self.model)
		self.clicked.connect(self.user_selected)
		self.adjustSize()

	def user_selected(self, index):
		return
		# TODO, FIXME, XXX: this dialog is disabled 'cause it's really WIP
		u = UserDetailsWindow(self.model.data(index, UserListModel.UserRole), False, self)
		u.show()

	def setUsers(self, users):
		self.model.setUsers(users)

class UserListWindow(QMainWindow):
	def __init__(self, title, users, parent):
		super(UserListWindow, self).__init__(parent)
		self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.setWindowTitle(title)

		self.cw = QWidget(self)
		self.setCentralWidget(self.cw)

		layout = QVBoxLayout(self.cw)

		self.text_field = QLineEdit(self)
		self.text_field.setPlaceholderText("Type to filter")
		self.list = UserList(users, self)

		self.text_field.textChanged.connect(self.filter)

		layout.addWidget(self.text_field)
		layout.addWidget(self.list)

		updateUsers = Signal()
		self.connect(self, SIGNAL("updateUsers()"), self._updateUsers)
		self.shown = False

	def show(self):
		super(UserListWindow, self).show()
		self.shown = True

	def _updateUsers(self):
		self.setUsers(self.parent().users())
		if not self.shown:
			self.show()

	def filter(self, text):
		self.list.filter(text)

	def setUsers(self, users):
		self.list.setUsers(users)
