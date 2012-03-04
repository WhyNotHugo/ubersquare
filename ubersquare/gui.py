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

import sys
from PySide.QtCore import *
from PySide.QtGui import *

from PySide.QtMaemo5 import QMaemo5ListPickSelector, QMaemo5ValueButton, QMaemo5InformationBox

import foursquare_auth
from venue_widgets import *
import foursquare
from locationProviders import *
from threads import VenueProviderThread, UserUpdaterThread, ImageCacheThread
from custom_widgets import SignalEmittingValueButton

class LocationProviderModel(QAbstractListModel):
	def __init__(self):
		super(LocationProviderModel, self).__init__()
		self.__locationProviders = LocationProvider()
		self.__locationProviders.init()

	def rowCount(self, role=Qt.DisplayRole):
		return self.__locationProviders.len()

	LocationProviderRole = 54351385

	def data(self, index, role=Qt.DisplayRole):
		lp = self.__locationProviders.get(index.row())
		if role == Qt.DisplayRole:
			return lp.get_name()
		if role == LocationProviderModel.LocationProviderRole:
			return lp

class LocationProviderSelector(QMaemo5ListPickSelector):
	def __init__(self):
		super(LocationProviderSelector, self).__init__()
		self.setModel(LocationProviderModel())
		
		# This restores the last selected provider
		previousIndex = foursquare.config_get("locationProvider");
		if not previousIndex:
			previousIndex = 0
		else:
			previousIndex = int(previousIndex)
		self.setCurrentIndex(previousIndex)
		LocationProvider().select(previousIndex)

class UserListModel(QAbstractListModel):
	def __init__(self, users):
		super(UserListModel, self).__init__()
		self.users = users

	UserRole = 54514533

	def rowCount(self, role=Qt.DisplayRole):
		return len(self.users)

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
			return user

	def setUsers(self, users):
		print "users updated int he model"
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
		# d = VenueDetailsWindow(self, self.proxy.data(index,VenueModel.VenueRole))
		# d.show()
		pass

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

	def _updateUsers(self):
		self.setUsers(self.parent().users())

	def filter(self, text):
		self.list.filter(text)

	def setUsers(self, users):
		self.list.setUsers(users)

class Profile(QWidget):
	def __init__(self, parent = None):
		super(Profile, self).__init__(parent)
		user = foursquare.get_user("self", True)[u'user']
		photo = QImage(foursquare.image(user[u'photo']))
		photo_label = QLabel()
		photo_label.setPixmap(QPixmap(photo))

		name = "<b>"
		if u'firstName' in user:
			name += user[u'firstName'] + " "
		if u'lastName' in user:
			name += user[u'lastName']
		name += "</b>"

		badges = str(user[u'badges'][u'count']) + " badges"
		mayorships = str(user[u'mayorships'][u'count']) + " mayorships"
		checkins = str(user[u'checkins'][u'count']) + " checkins"

		text = name + "<p>" + badges + "<br>" + mayorships + "<br>" + checkins 

		profileLayout = QGridLayout()
		self.setLayout(profileLayout)
		profileLayout.addWidget(photo_label, 0, 0)
		profileLayout.addWidget(QLabel(text), 0, 1, 1, 2)

class MainWindow(QMainWindow):

	def __init__(self):
		super(MainWindow, self).__init__(None)
		self.setAttribute(Qt.WA_Maemo5StackedWindow)
		self.setWindowTitle("UberSquare")

		self.centralWidget = QWidget() 
		self.setCentralWidget(self.centralWidget) 

		#Main Layout 
		layout = QVBoxLayout() 
		layout.setSpacing(0)         
		self.centralWidget.setLayout(layout) 

		#Content Layout 
		self.container = QWidget() 

		self.scrollArea = QScrollArea() 
		self.scrollArea.setWidget(self.container)           

		layout.addWidget(self.scrollArea)   

		self.scrollArea.setWidgetResizable(True)

		gridLayout = QGridLayout() 
		self.container.setLayout(gridLayout) 
		
		previous_venues_button = QPushButton("Visited")
		previous_venues_button.setIcon(QIcon.fromTheme("general_clock"))
		self.connect(previous_venues_button, SIGNAL("clicked()"), self.previous_venues_pushed)

		todo_venues_button = QPushButton("To-Do List")
		todo_venues_button.setIcon(QIcon.fromTheme("calendar_todo"))
		self.connect(todo_venues_button, SIGNAL("clicked()"), self.todo_venues_pushed)

		search_venues_button = QPushButton("Search/Explore")
		self.connect(search_venues_button, SIGNAL("clicked()"), self.search_venues_pushed)

		self.location_button = SignalEmittingValueButton("Location", self.locationSelected, self)
		self.location_button.setPickSelector(LocationProviderSelector())
		self.location_button.setValueLayout(QMaemo5ValueButton.ValueUnderTextCentered)

		images_button = QPushButton("Update image cache")
		self.connect(images_button, SIGNAL("clicked()"), self.imageCache_pushed)

		logout_button = QPushButton("Forget credentials")
		self.connect(logout_button, SIGNAL("clicked()"), self.logout_pushed)

		new_venue_button = QPushButton("Add")
		self.connect(new_venue_button, SIGNAL("clicked()"), self.new_venue_pushed)

		leaderboard_button = QPushButton("Leaderboard")
		self.connect(leaderboard_button, SIGNAL("clicked()"), self.leaderboard_button_pushed)

		row = 0
		gridLayout.addWidget(Profile(), row, 0, 3, 1)
		gridLayout.addWidget(QLabel("<b>Venues</b>"), row, 1, Qt.AlignHCenter)
		row += 1
		gridLayout.addWidget(previous_venues_button, row, 1)
		row += 1
		gridLayout.addWidget(todo_venues_button, row, 1)
		row += 1
		gridLayout.addWidget(leaderboard_button, row, 0)
		gridLayout.addWidget(search_venues_button, row, 1)
		row += 1
		gridLayout.addWidget(self.location_button, row, 0)
		gridLayout.addWidget(new_venue_button, row, 1)
		row += 1
		gridLayout.addWidget(QLabel("<b>Settings</b>"), row, 0, 1, 2, Qt.AlignHCenter)
		row += 1
		gridLayout.addWidget(images_button, row, 0)
		gridLayout.addWidget(logout_button, row, 1)

		self.setupMenu()
		self._venues = None

		networkError = Signal()
		self.connect(self, SIGNAL("networkError()"), self.__networkError)

		showSearchResults = Signal()
		self.connect(self, SIGNAL("showSearchResults()"), self.__showSearchResults)

		hideWaitingDialog = Signal()
		self.connect(self, SIGNAL("hideWaitingDialog()"), self.__hideWaitingDialog)

	def imageCache_pushed(self):
		c = QMessageBox(self)
		c.setWindowTitle("Update image cache?")
		c.setText("This will update all the category images in the cache. Make sure you have a good connection, and don't have to pay-by-megabyte")
		c.addButton("Yes", QMessageBox.YesRole)
		c.addButton("No", QMessageBox.NoRole)
		c.setIcon(QMessageBox.Question)
		c.exec_()
		if c.buttonRole(c.clickedButton()) == QMessageBox.YesRole:
			t = ImageCacheThread(self)
			t.start()
			self.waitDialog = QMessageBox(self)
			self.waitDialog.setWindowTitle("Please wait...")
			self.waitDialog.setText("This dialog will auto-close once downloading finishes.")
			self.waitDialog.exec_()

	def __hideWaitingDialog(self):
		print "hiding wait dialog!"
		self.waitDialog.hide()

	def __networkError(self):
		self.ibox = QMaemo5InformationBox()
		self.ibox.information(self, "Oops! I couldn't connect to foursquare.<br>Make sure you have a working internet connection.", 8000)

	def __showSearchResults(self):
		self.progressDialog().close()

	def setVenues(self, venues):
		self.__venues = venues

	def venues(self):
		return self.__venues

	def setUsers(self, venues):
		self.__users = venues

	def users(self):
		return self.__users

	def setupMenu(self):
		about = QAction(self)
		about.setText("About")

		settings = QAction(self)
		settings.setText("Settings")

		menubar = QMenuBar(self)
		self.setMenuBar(menubar)

		menubar.addAction(settings)
		menubar.addAction(about)

	def leaderboard_button_pushed(self):
		w = UserListWindow("Leaderboard", foursquare.users_leaderboard(True), self)
		t = UserUpdaterThread(w, foursquare.users_leaderboard, self)
		w.show()
		t.start()

	def logout_pushed(self):
		config_del("code")
		config_del("access_token")
		msgBox = QMessageBox()
		msgBox.setText("I've gotten rid of your credentials. I'm going to close now, and if you run me again, it'll be like our first time all over again. Bye!")
		msgBox.setWindowTitle("Credentials forgotten")
		msgBox.exec_()
		self.close()

	def previous_venues_pushed(self):
		try:
			a = VenueListWindow(self, "Previous Venues", foursquare.get_history(True))
			w = VenueProviderThread(a, foursquare.get_history, (False,), self)
			w.start()
			a.show()
		except IOError:
			self.network_error()

	def todo_venues_pushed(self):
		try:
			a = VenueListWindow(self, "To-Do Venues", foursquare.lists_todos(True))
			w = VenueProviderThread(a, foursquare.lists_todos, (False,), self)
			w.start()
			a.show()
		except IOError:
			self.network_error()

	def search_venues_pushed(self):
		d = QInputDialog(self)
		d.setInputMode(QInputDialog.TextInput)
		d.setLabelText("What do you want to search for?\n(Leave blank to explore)")
		d.setOkButtonText("Search")
		d.setWindowTitle("Search")
		if d.exec_() == 1:
			try:
				win = VenueListWindow(self, "Search results", foursquare.venues_search(d.textValue(), LocationProvider().get_ll()))
				win.show()
			except IOError:
				self.network_error()

	def network_error(self):
		self.ibox = QMaemo5InformationBox()
		self.ibox.information(self, "Oops! I couldn't connect to foursquare.<br>Make sure you have a working internet connection.", 15000)

	def locationSelected(self, index):
		LocationProvider().select(index)
		foursquare.config_set("locationProvider", index)

	def new_venue_pushed(self):
		w = NewVenueWindow(self, foursquare.get_venues_categories(), LocationProvider().get_ll())
		w.show()

def start():
	app = QApplication(sys.argv)

	token_present = foursquare.config_get("access_token") != None

	if not token_present:
		msgBox = QMessageBox()
		msgBox.setText("Hi! It looks like this is the first run!\n\nI'm going to open a browser window now, and I need you to authorize me so I can get data/do your check-ins, etc.")
		msgBox.setWindowTitle("First run")
		msgBox.addButton("Ok", QMessageBox.AcceptRole)
		msgBox.addButton("Cancel", QMessageBox.RejectRole)
		res = msgBox.exec_()
		if msgBox.buttonRole(msgBox.clickedButton()) == QMessageBox.AcceptRole:
			foursquare_auth.fetch_code()
			foursquare_auth.fetch_token()
			token_present = True
			d = QMessageBox()
			d.setWindowTitle("Image cache")
			d.setText("In order to save bandwidth, category images are cached.  To download these images for a first time, click \"Update image cache\". This'll take some time, but will <b>really</b> speed up searches.")
			d.addButton( "Ok", QMessageBox.YesRole)
			d.exec_()

	if token_present:
		main_window = MainWindow()
		main_window.show()
 
	sys.exit(app.exec_())

if __name__ == '__main__':
	start()