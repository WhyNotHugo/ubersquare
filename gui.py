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


class CheckinConfirmation(QMessageBox):

	def __init__(self, parent, venue):
		super(CheckinConfirmation, self).__init__(parent)
		
		self.setWindowTitle("Confirmation")
		text = "Do you want to check-in at <b>" + venue[u'name'] + "</b>"
		if u'address' in venue[u'location']:
			text += " located at " + venue[u'location'][u'address']	
		text += "?"
		self.setText(text)

		self.addButton("Yes", QMessageBox.YesRole)
		self.addButton("No", QMessageBox.NoRole)
		self.setIcon(QMessageBox.Question)

class CheckinDetails(QDialog):

	def __init__(self, parent, checking_details):

		super(CheckinDetails, self).__init__(parent)
		self.checking_details = checking_details
		self.setWindowTitle("Check-in successful")

		text = ""
		for item in checking_details[u'notifications']:
			if item[u'type'] == "message":
				text = item[u'item'][u'message'] + "<p>"
			elif item[u'type'] == "score":
				text += "Total points: %d" % item[u'item'][u'total']
				for score in item[u'item'][u'scores']:
					text += "<br>%(points)d  %(message)s" % \
					{'points': score[u'points'], 'message' : score[u'message']}

		vbox = QVBoxLayout()
		vbox.addWidget(QLabel(text))
 	
		ok_button = QPushButton("Ok")
		self.connect(ok_button, SIGNAL("clicked()"), self.close)
 
		vbox.addWidget(ok_button)
		self.setLayout(vbox)

class VenueModel(QAbstractListModel):
	def __init__(self, venues):
		super(VenueModel, self).__init__()
		self.venues = venues

	def rowCount(self, role=Qt.DisplayRole):
		return len(self.venues)

	def data(self, index, role=Qt.DisplayRole):
		if role == Qt.DisplayRole:
			venue = self.venues[index.row()][u'venue']
			if u'address' in venue[u'location']:
				return venue[u'name'] + "\n  " + venue[u'location'][u'address']
			else:
				return venue[u'name']

	def get_venue(self, index):
		return self.venues[index.row()][u'venue']

class VenueList(QListView):
	def __init__(self, parent, venues, callback):
		super(VenueList,self).__init__(parent)
		self.model = VenueModel(venues)
		self.setModel(self.model)
		self.clicked.connect(self.venue_selected)
		self.callback = callback


	def venue_selected(self, index):
		venue = self.model.get_venue(index)
		self.callback(self, venue)

class VenueWindow(QMainWindow):
	def __init__(self, parent, title, venues, callback):
		super(VenueWindow, self).__init__(parent)
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.setWindowTitle(title)

		self.cw = VenueList(self, venues, callback)
		self.setCentralWidget(self.cw)

class VenueDetailsWindow(QMainWindow):
	def __init__(self, parent, venue):
		super(VenueDetailsWindow, self).__init__(parent)
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)
		self.venue = venue

		self.setWindowTitle(venue[u'name'])

		self.cw = QWidget(self)
		self.setCentralWidget(self.cw)

		layout = QGridLayout(self.cw)

		if u'crossStreet' in venue[u'location']:
			crossStreet = ", " + venue[u'location'][u'crossStreet']
		else:
			crossStreet = ""

		checkin_button = QPushButton("Check-in")
		#checkin_button.setIcon(QIcon.fromTheme("general_clock"))
		self.connect(checkin_button, SIGNAL("clicked()"), self.checkin)

		layout.addWidget(checkin_button, 0, 0, 1, 3)
		layout.addWidget(QLabel("<b>" + venue[u'name'] + "</b>", self), 1, 0)
		layout.addWidget(QLabel(venue[u'location'][u'address'] + crossStreet, self), 2, 0)
		for item in venue[u'categories']:
			if item[u'primary'] == "true":
				layout.addWidget(QLabel(item[u'name'], self), 3, 0)
		layout.addWidget(QLabel("Total Checkins: " + str(venue[u'stats'][u'checkinsCount']), self), 4, 0)
		layout.addWidget(QLabel("Total Users: " + str(venue[u'stats'][u'usersCount']), self), 5, 0)
		if u'beenHere' in venue:
			if venue[u'beenHere'] == 1:
				times = "time"
			else:
				times = "times"
			layout.addWidget(QLabel("You've been here " + str(venue[u'beenHere']) + " " + times, self), 6, 0)

		full_venue_button = QPushButton("More... (TODO)")
		#checkin_button.setIcon(QIcon.fromTheme("general_clock"))
		#self.connect(checkin_button, SIGNAL("clicked()"), self.checkin)

		layout.addWidget(full_venue_button, 7, 0, 1, 3)

		layout.setRowStretch(8, 5)

	def checkin(self):
		c = CheckinConfirmation(self, self.venue)
		c.exec_()
		if c.buttonRole(c.clickedButton()) == QMessageBox.YesRole:
			ll = get_aproximate_location(self.venue)
			response = checkin(self.venue, ll)
			CheckinDetails(self, response).show()

class MainWindow(QMainWindow):

	def __init__(self):
		super(MainWindow, self).__init__(None)
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.venue_click_handler = self.venue_details #checkin

		self.cw = QWidget(self)
		self.setCentralWidget(self.cw)

		# menubar = QMenuBar(self)
		# menu_File = QMenu(menubar)
		self.setWindowTitle("UberSquare")
		vbox = QVBoxLayout(self.cw)
		
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

		vbox.addWidget(previous_venues_button)
		vbox.addWidget(todo_venues_button)
		vbox.addWidget(search_venues_button)
		vbox.addWidget(location_button)
		vbox.addStretch()

	def previous_venues_pushed(self):
		self.working()
		try:
			a = VenueWindow(self, "Previous Venues", get_history(), self.venue_click_handler)
			a.show()
		except IOError:
			network_error()

	def todo_venues_pushed(self):
		self.working()
		try:
			a = VenueWindow(self, "To-Do Venues", get_todo_venues(), self.venue_click_handler)
			a.show()
		except IOError:
			network_error()

	def search_venues_pushed(self):
		d = QInputDialog(self)
		d.setInputMode(QInputDialog.TextInput)
		d.setLabelText("What do you want to search for?\n(Leave blank to explore)")
		d.setOkButtonText("Search")
		d.setWindowTitle("Search")
		if d.exec_() == 1:
			self.working()
			try:
				win = VenueWindow(self, "Search results", venues_search(d.textValue(), locationProvider.get_ll()), self.venue_click_handler)
				win.show()
			except IOError:
				network_error()

	def network_error(self):
		#TODO: pynofity
		if maemo:
			self.ibox = QMaemo5InformationBox()
			self.ibox.information(self, "Oops! I couldn't connect to foursquare.<br>Make sure you have a working internet connection.", 15000)

	def working(self):
		#TODO: pynofity
		if maemo:
			self.ibox = QMaemo5InformationBox()
			self.ibox.information(self, "Working...", 1100)		

	def location_pushed(self):
		pass

	def checkin(self, parent_window, venue):
		c = CheckinConfirmation(parent_window, venue)
		c.exec_()
		if c.buttonRole(c.clickedButton()) == QMessageBox.YesRole:
			ll = get_aproximate_location(venue)
			response = checkin(venue, ll)
			CheckinDetails(parent_window, response).show()

	def venue_details(self, parent_window, venue):
		d = VenueDetailsWindow(parent_window, venue)
		d.show()
			
		
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