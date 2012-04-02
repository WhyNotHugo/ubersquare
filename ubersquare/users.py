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
from custom_widgets import UberSquareWindow, Title
from threads import UserDetailsThread
import foursquare
from datetime import datetime
import time

from venues import CheckinConfirmation, CheckinDetails
from locationProviders import LocationProvider


class UserProfile(QWidget):
	def __init__(self, user, parent=None):
		super(UserProfile, self).__init__(parent)

		name = user[u'user'][u'firstName']
		if u'lastName' in user[u'user']:
			name += " " + user[u'user'][u'lastName']

		description = ""
		if u'homeCity' in user[u'user']:
			description += "From " + user[u'user'][u'homeCity']

		location = ""
		# FIXME: this may fail!
		location = user[u'user'][u'checkins'][u'items'][0][u'venue'][u'name']
		lastSeen = user[u'user'][u'checkins'][u'items'][0][u'createdAt']
		lastSeen = datetime.fromtimestamp(lastSeen).strftime("%Y-%m-%d %X")
		location = "Last seen at <b>" +  location + "</b>, at <i>" + lastSeen + "</i>"

		description = description + "<br>" + location

		self.descriptionLabel = QLabel(description)
		self.descriptionLabel.setWordWrap(True)

		self.photo_label = QLabel()
		self.photo = QImage(foursquare.image(user[u'user'][u'photo']))
		self.photo_label.setPixmap(QPixmap(self.photo))

		profileLayout = QGridLayout()
		self.setLayout(profileLayout)

		profileLayout.addWidget(self.photo_label, 0, 0, 2, 1)
		profileLayout.addWidget(Title(name), 0, 1)
		profileLayout.addWidget(self.descriptionLabel, 1, 1)

		profileLayout.setColumnStretch(1, 5)


class UserDetailsWindow(UberSquareWindow):
	def __init__(self, user, parent):
		super(UserDetailsWindow, self).__init__(parent)

		self.user = user

		self.centralWidget = QWidget()
		self.setCentralWidget(self.centralWidget)

		layout = QVBoxLayout()
		layout.setSpacing(0)
		layout.setContentsMargins(11, 11, 11, 11)
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
		gridLayout.addWidget(UserProfile(user), i, 0, 1, 2)

		### checkin button
		if user[u'user'][u'relationship'] != "self":
			i += 1
			self.shoutText = QLineEdit(self)
			self.shoutText.setPlaceholderText("Shout something")
			gridLayout.addWidget(self.shoutText, i, 0)

			checkinButton = QPushButton("Check-in with " + firstName)
			self.connect(checkinButton, SIGNAL("clicked()"), self.checkin)
			gridLayout.addWidget(checkinButton, i, 1)

		if user[u'user'][u'relationship'] == "friend":
			i += 1
			#gridLayout.addWidget(QPushButton("Unfriend"), i, 0, 1, 2)
			gridLayout.addWidget(QLabel("TODO: Unfriend"), i, 0, 1, 2)
		elif user[u'user'][u'relationship'] == "self":
			i += 1
			gridLayout.addWidget(QLabel("It's you!"), i, 0, 1, 2)
		if user[u'user'][u'id'] == "17270875":
			i += 1
			gridLayout.addWidget(QLabel("<b>This is the UberSquare developer!</b>"), i, 0, 1, 2)

		i += 1
		checkins = user[u'user'][u'checkins'][u'count']
		gridLayout.addWidget(QLabel(str(checkins) + " checkins"), i, 0)
		i += 1
		badges = user[u'user'][u'badges'][u'count']
		gridLayout.addWidget(QLabel(str(badges) + " badges"), i, 0)
		i += 1
		mayorships = user[u'user'][u'mayorships'][u'count']
		gridLayout.addWidget(QLabel(str(mayorships) + " mayorships"), i, 0)
		i += 1
		gridLayout.addWidget(QPushButton("TODO: See places " + firstName + " has been to."), i, 0, 1, 2)

		i += 1
		update_user_button = QPushButton("Refresh user details")
		update_user_button.setIcon(QIcon.fromTheme("general_refresh"))
		self.connect(update_user_button, SIGNAL("clicked()"), self.__update)
		gridLayout.addWidget(update_user_button, i, 0, 1, 2)

		showUser = Signal()
		self.connect(self, SIGNAL("showUser()"), self.__showUser)

	def __update(self):
		print "updating..."
		t = UserDetailsThread(self.user[u'user'][u'id'], self)
		t.start()
		self.showWaitingDialog.emit()

	def __showUser(self):
		time.sleep(0.15)
		self.close()
		self.uid = self.user[u'user'][u'id']
		user = foursquare.get_user(self.uid, foursquare.CacheOrNull)
		if user:
			self.userWindow = UserDetailsWindow(user, self)
			self.userWindow.show()

	def checkin(self):
		venue = self.user[u'user'][u'checkins'][u'items'][0][u'venue']

		c = CheckinConfirmation(self, venue)
		c.exec_()
		if c.buttonRole(c.clickedButton()) == CheckinConfirmation.YesRole:
			try:
				# TODO: do this in a separate thread
				ll = LocationProvider().get_ll(venue)
				response = foursquare.checkin(venue, ll, self.shoutText.text())
				CheckinDetails(self, response).show()
			except IOError:
				self.networkError.emit()


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
		super(UserList, self).__init__(parent)
		self.model = UserListModel(users)
		self.setModel(self.model)
		self.clicked.connect(parent.user_selected)
		self.adjustSize()
	
	def setUsers(self, users):
		self.model.setUsers(users)

	def getUser(self, index):
		return self.model.data(index, UserListModel.UserRole)


class UserListWindow(UberSquareWindow):
	def __init__(self, title, users, parent):
		super(UserListWindow, self).__init__(parent)

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

	def _updateUsers(self):
		self.setUsers(self.parent().users())
		if not self.shown:
			self.show()

	def filter(self, text):
		self.list.filter(text)

	def setUsers(self, users):
		self.list.setUsers(users)

		showUser = Signal()
		self.connect(self, SIGNAL("showUser()"), self.__showUser)

	def user_selected(self, index):
		self.uid = self.list.getUser(index)[u'user'][u'id']
		user = foursquare.get_user(self.uid, foursquare.CacheOrNull)

		if user:
			self.userWindow = UserDetailsWindow(user, self)
			self.userWindow.show()
		else:
			t = UserDetailsThread(self.uid, self)
			t.start()

	def __showUser(self):
		user = foursquare.get_user(self.uid, foursquare.CacheOrNull)
		self.userWindow = UserDetailsWindow(user, self)
		self.userWindow.show()
