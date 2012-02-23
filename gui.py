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
from venue_widgets import *
import foursquare
import locationProviders

locationProvider = locationProviders.LastCheckinLocationProvider()






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


	def filter(self, text):
		self.list.filter(text)

	def setUsers(self, users):
		self.list.setUsers(users)












































class VenueProviderThread(QThread):
	"""
	Retrieves venues from source with args on a background thread, and then passes it over to target using the setVenues method
	"""
	def __init__(self, target, source, args):
		super(VenueProviderThread, self).__init__()
		self.target = target
		self.source = source
		self.args = args
	
	def run(self):
		# try:
		venues = self.source(*self.args)
		self.target.setVenues(venues)
		# except IOError:
		# 	self.ibox = QMaemo5InformationBox()
		# 	self.ibox.information(self.target, "Oops! I couldn't connect to foursquare.<br>Make sure you have a working internet connection.", 5000)
		self.exec_()
		self.exit(0)

class MainWindow(QMainWindow):

	def __init__(self):
		super(MainWindow, self).__init__(None)
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)
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

		location_button = QPushButton("Location")
		location_button.setIcon(QIcon.fromTheme("gps_location"))
		self.connect(location_button, SIGNAL("clicked()"), self.location_pushed)

		new_venue_button = QPushButton("Add")
		self.connect(new_venue_button, SIGNAL("clicked()"), self.new_venue_pushed)

		leaderboard_button = QPushButton("Leaderboard")
		self.connect(leaderboard_button, SIGNAL("clicked()"), self.leaderboard_button_pushed)


		profile = QWidget()

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
		profile.setLayout(profileLayout)
		profileLayout.addWidget(photo_label, 0, 0)
		profileLayout.addWidget(QLabel(text), 0, 1, 1, 2)

		row = 0
		gridLayout.addWidget(profile, row, 0, 3, 1)
		gridLayout.addWidget(QLabel("<b>Venues</b>"), row, 1, Qt.AlignHCenter)
		row += 1
		gridLayout.addWidget(previous_venues_button, row, 1)
		row += 1
		gridLayout.addWidget(todo_venues_button, row, 1)
		row += 1
		gridLayout.addWidget(leaderboard_button, row, 0)
		gridLayout.addWidget(search_venues_button, row, 1)
		row += 1
		gridLayout.addWidget(new_venue_button, row, 1)
		row += 1
		gridLayout.addWidget(QLabel("<b>Settings</b>"), row, 1, Qt.AlignHCenter)
		row += 1
		gridLayout.addWidget(location_button, row, 1)

	def leaderboard_button_pushed(self):
		w = UserListWindow("Leaderboard", foursquare.users_leaderboard(False), self)
		w.show();
		# TODO: background update

	def previous_venues_pushed(self):
		try:
			a = VenueListWindow(self, "Previous Venues", get_history(True))
			w = VenueProviderThread(a, get_history, (False,))
			w.start()
			a.show()
		except IOError:
			self.network_error()

	def todo_venues_pushed(self):
		try:
			a = VenueListWindow(self, "To-Do Venues", get_todo_venues(True))
			w = VenueProviderThread(a, get_todo_venues, (False,))
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
				win = VenueListWindow(self, "Search results", venues_search(d.textValue(), locationProvider.get_ll()))
				win.show()
			except IOError:
				self.network_error()

	def network_error(self):
		#TODO: pynofity
		if maemo:
			self.ibox = QMaemo5InformationBox()
			self.ibox.information(self, "Oops! I couldn't connect to foursquare.<br>Make sure you have a working internet connection.", 15000)

	def location_pushed(self):
		pass

	def new_venue_pushed(self):
		w = NewVenueWindow(self, foursquare.get_venues_categories(), foursquare.get_last_ll())
		w.show()

if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.show()
 
	sys.exit(app.exec_())