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

import sys
from PySide.QtCore import *
from PySide.QtGui import *

from PySide.QtMaemo5 import QMaemo5ListPickSelector, QMaemo5ValueButton, QMaemo5InformationBox

import foursquare_auth
from venue_widgets import *
import foursquare
from foursquare import Cache
from locationProviders import LocationProviderSelector, LocationProvider
from threads import VenueProviderThread, UserUpdaterThread, ImageCacheThread, UpdateSelf
from custom_widgets import SignalEmittingValueButton, WaitingDialog

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

class Profile(QWidget):
	def __init__(self, parent = None):
		super(Profile, self).__init__(parent)
		self.user = foursquare.get_user("self", Cache.CacheOrGet)[u'user']
		photo = QImage(foursquare.image(self.user[u'photo']))
		photo_label = QLabel()
		photo_label.setPixmap(QPixmap(photo))

		self.textLabel = QLabel()
		self.__updateInfo(True)

		profileLayout = QGridLayout()
		self.setLayout(profileLayout)
		profileLayout.addWidget(photo_label, 0, 0)
		profileLayout.addWidget(self.textLabel, 0, 1, 1, 2)

		clicked = Signal()
		self.connect(self, SIGNAL("clicked()"), self.__clicked)

		selfUpdated = Signal()
		self.connect(self, SIGNAL("selfUpdated()"), self.__updateInfo)
		# networkError = Signal()

	# def __networkError

	def __clicked(self):
		t = UpdateSelf(self)
		t.start()
		QMaemo5InformationBox.information(self, "Updating info...", 1500)

	def mousePressEvent(self, event):
		self.clicked.emit()

	def __updateInfo(self, initial = False):
		if not initial:
			QMaemo5InformationBox.information(self, "Info updated!", 1500)
		name = "<b>"
		if u'firstName' in self.user:
			name += self.user[u'firstName'] + " "
		if u'lastName' in self.user:
			name += self.user[u'lastName']
		name += "</b>"

		badges = str(self.user[u'badges'][u'count']) + " badges"
		mayorships = str(self.user[u'mayorships'][u'count']) + " mayorships"
		checkins = str(self.user[u'checkins'][u'count']) + " checkins"

		text = name + "<p>" + badges + "<br>" + mayorships + "<br>" + checkins

		self.textLabel.setText(text)

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

		showWaitingDialog = Signal()
		self.connect(self, SIGNAL("showWaitingDialog()"), self.__showWaitingDialog)

		self.waitDialog = WaitingDialog(self)

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
		self.connect(about, SIGNAL("triggered()"), self.__showAbout)

		settings = QAction(self)
		settings.setText("Settings")

		menubar = QMenuBar(self)
		self.setMenuBar(menubar)

		menubar.addAction(settings)
		menubar.addAction(about)

	def __showAbout(self):
		title = "About UberSquare"
		aboutText = """
UberSquare is a foursquare for maemo, specifically, for the Nokia N900.  Be sure to report any bugs you may find, and feel free to email me if you have any suggestions, etc.
"""

		bsdLicense = """
Copyright (c) 2012 Hugo Osvaldo Barrera <hugo@osvaldobarrera.com.ar>

Permission to use, copy, modify, and distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""
		foursquareDisclaimer = """
This application uses the foursquare(r) application programming interface but is not endorsed or certified by Foursquare Labs, Inc.  All of the foursquare(r) logos (including all badges) and trademarks displayed on this application are the property of Foursquare Labs, Inc.
"""

		dialog = QDialog()
		dialog.setWindowTitle(title)
		dialog.centralWidget = QWidget() 

		#Main Layout 
		layout = QVBoxLayout() 
		layout.setSpacing(0)         
		dialog.setLayout(layout) 

		#Content Layout 
		self.container = QWidget() 

		self.scrollArea = QScrollArea() 
		self.scrollArea.setWidget(self.container)           

		layout.addWidget(self.scrollArea)   

		self.scrollArea.setWidgetResizable(True)

		gridLayout = QGridLayout() 
		self.container.setLayout(gridLayout) 

		aboutTextLabel = QLabel(aboutText)
		aboutTextLabel.setWordWrap(True)

		bsdLicenseLabel = QLabel(bsdLicense)
		bsdLicenseLabel.setWordWrap(True)

		foursquareDisclaimerLabel = QLabel(foursquareDisclaimer)
		foursquareDisclaimerLabel.setWordWrap(True)

		gridLayout.addWidget(aboutTextLabel, 0, 0)
		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setMaximumWidth(QApplication.desktop().screenGeometry().width() * 0.5)
		gridLayout.addWidget(line, 1, 0)

		gridLayout.addWidget(bsdLicenseLabel, 2, 0)
		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setMaximumWidth(QApplication.desktop().screenGeometry().width() * 0.5)
		gridLayout.addWidget(line, 3, 0)

		gridLayout.addWidget(foursquareDisclaimerLabel, 4, 0)
		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setMaximumWidth(QApplication.desktop().screenGeometry().width() * 0.5)
		gridLayout.addWidget(line, 5, 0)

		gridLayout.addWidget(QLabel("TODO: Insert \"powered by foursquare\" image here."), 6, 0)

		dialog.exec_()

	def leaderboard_button_pushed(self):
		users = foursquare.users_leaderboard(foursquare.CacheOrNull)
		w = UserListWindow("Leaderboard", users, self)
		t = UserUpdaterThread(w, foursquare.users_leaderboard, self)
		t.start()
		if users:
			w.show()
		else:
			self.__showWaitingDialog()

	def logout_pushed(self):
		config_del("code")
		config_del("access_token")
		msgBox = QMessageBox()
		msgBox.setText("I've gotten rid of your credentials. I'm going to close now, and if you run me again, it'll be like our first time all over again. Bye!")
		msgBox.setWindowTitle("Credentials forgotten")
		msgBox.exec_()
		self.close()

	def previous_venues_pushed(self):
		venues = foursquare.get_history(foursquare.CacheOrNull)
		w = VenueListWindow("Previous Venues", venues, self)
		t = VenueProviderThread(w, foursquare.get_history, self)
		t.start()
		if venues:
			w.show()
		else:
			self.__showWaitingDialog()

	def todo_venues_pushed(self):
		try:
			venues = foursquare.lists_todos(foursquare.CacheOrNull)
			w = VenueListWindow("To-Do Venues", venues, self)
			t = VenueProviderThread(w, foursquare.lists_todos, self)
			t.start()
			if venues:
				w.show()
			else:
				self.__showWaitingDialog()
		except IOError:
			self.networkError.emit()

	def search_venues_pushed(self):
		d = QInputDialog(self)
		d.setInputMode(QInputDialog.TextInput)
		d.setLabelText("What do you want to search for?\n(Leave blank to explore)")
		d.setOkButtonText("Search")
		d.setWindowTitle("Search")
		if d.exec_() == 1:
			try:
				win = VenueListWindow("Search results", foursquare.venues_search(d.textValue(), LocationProvider().get_ll()), self)
				win.show()
			except IOError:
				self.networkError.emit()

	def locationSelected(self, index):
		LocationProvider().select(index)
		foursquare.config_set("locationProvider", index)

	def new_venue_pushed(self):
		try:
			w = NewVenueWindow(self, foursquare.get_venues_categories(), LocationProvider().get_ll())
			w.show()
		except IOError:
			self.networkError.emit()

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
		try:
			foursquare.get_user("self", Cache.CacheOrGet)
		except IOError:
			d = QMessageBox()
			d.setWindowTitle("Network Error")
			d.setText("I couldn't connect to foursquare to retrieve data. Make sure you're connected to the internet, and try again (keep in mind that it may have been just a network glitch).")
			d.addButton( "Ok", QMessageBox.YesRole)
			d.exec_()
			
		main_window = MainWindow()
		main_window.show()
 
	sys.exit(app.exec_())

if __name__ == '__main__':
	start()