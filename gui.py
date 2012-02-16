import sys
from PySide.QtCore import *
from PySide.QtGui import *
try:
	from PySide.QtMaemo5 import *
	maemo = True
except ImportError:
	print "Couldn't import QtMaemo5. You're probably not running on maemo."
	print "I'll probably crash at some point, though some stuff will work."
	maemo = False
try:
	import location
except ImportError:
	print "Couldn't import location. You're probably not running maemo."
	print "GPS Support disabled."

from foursquare import *
from venue_widgets import *
import foursquare

locationProvider = None

class FullAGPSLocationProvider:
	def __init__(self):
		try:
			self.control = location.GPSDControl.get_default()
			self.device = location.GPSDevice()

			self.control.set_properties(preferred_method=location.METHOD_ACWP|location.METHOD_AGNSS)
		except NameError:
			return

	def get_ll(self):
		lat = "%2.8f" % self.device.fix[4]
		lng = "%2.8f" % self.device.fix[5]
		return lat + "," + lng

class VenueProviderThread(QThread):
	def __init__(self, target, source, args):
		super(VenueProviderThread, self).__init__()
		self.target = target
		self.source = source
		self.args = args
	
	def run(self):
		venues = self.source(*self.args)
		self.target.setVenues(venues)
		self.exec_()
		self.exit(0)

class MainWindow(QMainWindow):

	def __init__(self):
		super(MainWindow, self).__init__(None)
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.cw = QWidget(self)
		self.setCentralWidget(self.cw)

		# menubar = QMenuBar(self)
		# menu_File = QMenu(menubar)
		self.setWindowTitle("UberSquare")
		vbox = QGridLayout(self.cw)
		
		previous_venues_button = QPushButton("Previous Venues")
		previous_venues_button.setIcon(QIcon.fromTheme("general_clock"))
		self.connect(previous_venues_button, SIGNAL("clicked()"), self.previous_venues_pushed)

		todo_venues_button = QPushButton("To-Do List Venues")
		todo_venues_button.setIcon(QIcon.fromTheme("calendar_todo"))
		self.connect(todo_venues_button, SIGNAL("clicked()"), self.todo_venues_pushed)

		search_venues_button = QPushButton("Search Venues")
		#search_venues_button.setIcon(QIcon.fromTheme("calendar_todo"))
		self.connect(search_venues_button, SIGNAL("clicked()"), self.search_venues_pushed)

		location_button = QPushButton("Location")
		location_button.setIcon(QIcon.fromTheme("gps_location"))
		self.connect(location_button, SIGNAL("clicked()"), self.location_pushed)

		vbox.addWidget(QPushButton("Me"), 0, 0, 4, 1)
		vbox.addWidget(previous_venues_button, 0, 1)
		vbox.addWidget(todo_venues_button, 1, 1)
		vbox.addWidget(search_venues_button, 2, 1)
		vbox.addWidget(location_button, 3, 1)
		vbox.setRowStretch(4, 5)

	def previous_venues_pushed(self):
		try:
			a = VenueWindow(self, "Previous Venues", get_history(True))
			w = VenueProviderThread(a, get_history, (False,))
			w.start()
			a.show()
		except IOError:
			self.network_error()

	def todo_venues_pushed(self):
		try:
			a = VenueWindow(self, "To-Do Venues", get_todo_venues(True))
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
				win = VenueWindow(self, "Search results", venues_search(d.textValue(), locationProvider.get_ll()))
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

	def checkin(self, parent_window, venue):
		c = CheckinConfirmation(parent_window, venue)
		c.exec_()
		if c.buttonRole(c.clickedButton()) == QMessageBox.YesRole:
			ll = get_aproximate_location(venue)
			response = checkin(venue, ll)
			CheckinDetails(parent_window, response).show()

# class QueryDialog(QDialog):
# 	def __init__(self, parent, text, button_text):
# 		super(QueryDialog, self).__init__(parent)
# 		self.setWindowTitle("Input")
# 		vbox = QVBoxLayout(self)
	
# 		label = QLabel(text, self)
# 		button = QPushButton(button_text, self)

# 		text_field = QInputDialog(self)

# 		self.connect(button, SIGNAL("clicked()"), self.close)

# 		vbox.addWidget(label)
# 		vbox.addWidget(text_field)
# 		vbox.addWidget(button)
# 		self.setLayout(vbox)
		
if __name__ == '__main__':
	locationProvider = FullAGPSLocationProvider()

	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.show()
 
	sys.exit(app.exec_())