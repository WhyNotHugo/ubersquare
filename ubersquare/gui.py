import sys
sys.path.append('/home/user/ubersquare')
from PySide.QtCore import *
from PySide.QtGui import *

try:
	from PySide.QtMaemo5 import *
	maemo = True
except ImportError:
	print "Couldn't import QtMaemo5. You're probably not running on maemo."
	print "I'll probably crash at some point, though some stuff will work."
	maemo = False

from foursquare import *
import foursquare_auth
from venue_widgets import *
import foursquare
from locationProviders import *
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
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.setWindowTitle(title)

		self.cw = QWidget(self)
		self.setCentralWidget(self.cw)

		layout = QVBoxLayout(self.cw)

		# self.text_field = QLineEdit(self) #QPlainTextEdit es multilinea
		# self.text_field.setPlaceholderText("Type to filter")
		self.list = UserList(users, self)

		#self.text_field.textChanged.connect(self.filter)

		#layout.addWidget(self.text_field)
		layout.addWidget(self.list)

		updateUsers = Signal()
		self.connect(self, SIGNAL("updateUsers()"), self._updateUsers)

	def _updateUsers(self):
		self.setUsers(self.parent().users())

	def filter(self, text):
		self.list.filter(text)

	def setUsers(self, users):
		self.list.setUsers(users)

class VenueProviderThread(QThread):
	"""
	Retrieves venues from source with args on a background thread, and then passes it over to target using the setVenues method
	"""
	def __init__(self, target, source, args, parent):
		super(VenueProviderThread, self).__init__()
		self.target = target
		self.source = source
		self.args = args
		self.parentWindow = parent
	
	def run(self):
		try:
			venues = self.source(*self.args)
			self.parentWindow.setVenues(venues)
			self.target.updateVenues.emit()
		except IOError:
			self.parentWindow.networkError.emit()
		self.exec_()
		self.exit(0)

class UserUpdaterThread(QThread):
	"""
	Retrieves users from source with args on a background thread, and then passes it over to target using the setUsers method
	"""
	def __init__(self, target, source, args, parent):
		super(UserUpdaterThread, self).__init__()
		self.target = target
		self.source = source
		self.args = args
		self.parentWindow = parent
	
	def run(self):
		try:
			users = self.source(*self.args)
			self.parentWindow.setUsers(users)
			self.target.updateUsers.emit()
		except IOError:
			self.parentWindow.networkError.emit()
		self.exec_()
		self.exit(0)


class Profile(QWidget):
	def __init__(self, parent = None):
		super(Profile, self).__init__(parent)
		user = foursquare.get_user("self", True)[u'user']
		photo = QImage(foursquare.image(user[u'photo']))
		#photo.load()
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
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)
		#self.setAttribute(Qt.WA_Maemo5AutoOrientation, True)
		self.setWindowTitle("UberSquare")
		#layout.setContentsMargins

		# self.cw = QWidget(self)
		# self.setCentralWidget(self.cw)
		# gridLayout = QGridLayout(self.cw)

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
		#location_button.setIcon(QIcon.fromTheme("gps_location"))
		self.location_button.setPickSelector(LocationProviderSelector())
		self.location_button.setValueLayout(QMaemo5ValueButton.ValueUnderTextCentered)
		#self.location_button.setValueLayout(QMaemo5ValueButton.ValueBesideText)

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
		gridLayout.addWidget(QLabel("<b>Settings</b>"), row, 1, Qt.AlignHCenter)
		row += 1
		gridLayout.addWidget(logout_button, row, 1)

		self.setupMenu()
		self._venues = None

		networkError = Signal()
		self.connect(self, SIGNAL("networkError()"), self.__networkError)

		showSearchResults = Signal()
		self.connect(self, SIGNAL("showSearchResults()"), self.__showSearchResults)

	def __networkError(self):
		self.ibox = QMaemo5InformationBox()
		self.ibox.information(self, "Oops! I couldn't connect to foursquare.<br>Make sure you have a working internet connection.", 5000)

	def __showSearchResults(self):
		self.progressDialog().close()
		# win = VenueListWindow(self, "Search results", venues_search(d.textValue(), LocationProvider().get_ll()))
		# win.show()

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
		t = UserUpdaterThread(w, users_leaderboard, (False,), self)
		t.start()
		w.show();

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
			a = VenueListWindow(self, "Previous Venues", get_history(True))
			w = VenueProviderThread(a, get_history, (False,), self)
			w.start()
			a.show()
		except IOError:
			self.network_error()

	def todo_venues_pushed(self):
		try:
			a = VenueListWindow(self, "To-Do Venues", get_todo_venues(True))
			w = VenueProviderThread(a, get_todo_venues, (False,), self)
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
				win = VenueListWindow(self, "Search results", venues_search(d.textValue(), LocationProvider().get_ll()))
				win.show()
			except IOError:
				self.network_error()

	def network_error(self):
		#TODO: pynofity
		if maemo:
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

	token_present = config_get("access_token") != None

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

	if token_present:
		main_window = MainWindow()
		main_window.show()
 
	sys.exit(app.exec_())

if __name__ == '__main__':
	start()