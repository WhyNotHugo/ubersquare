from PySide.QtCore import *
from PySide.QtGui import *
from foursquare import *

try:
	from PySide.QtMaemo5 import *
	maemo = True
except ImportError:
	maemo = False

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
					text += "<br>+%(points)d   %(message)s" % \
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

	VenueRole = 849561745

	def rowCount(self, role=Qt.DisplayRole):
		return len(self.venues)

	def data(self, index, role=Qt.DisplayRole):
		if role == Qt.DisplayRole:
			venue = self.venues[index.row()][u'venue']
			if u'address' in venue[u'location']:
				return venue[u'name'] + "\n  " + venue[u'location'][u'address']
			else:
				return venue[u'name']
		if role == VenueModel.VenueRole:
			return self.venues[index.row()][u'venue']

	def setVenues(self, venues):
		self.venues = venues
		self.reset()

class VenueList(QListView):
	def __init__(self, parent, venues):
		super(VenueList,self).__init__(parent)
		self.model = VenueModel(venues)
		#self.setModel(self.model)
		
		self.proxy = QSortFilterProxyModel(self)
		self.proxy.setSourceModel(self.model)
		self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
		self.setModel(self.proxy)

		self.clicked.connect(self.venue_selected)

	def venue_selected(self, index):
		d = VenueDetailsWindow(self, self.proxy.data(index,VenueModel.VenueRole))
		d.show()

	def filter(self,text):
		self.proxy.setFilterRegExp(text)
		self.proxy.filterRegExp()

	def setVenues(self, venues):
		self.model.setVenues(venues)

class VenueWindow(QMainWindow):
	def __init__(self, parent, title, venues):
		super(VenueWindow, self).__init__(parent)
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.setWindowTitle(title)

		self.cw = QWidget(self)
		self.setCentralWidget(self.cw)

		layout = QVBoxLayout(self.cw)

		self.text_field = QLineEdit(self) #QPlainTextEdit es multilinea
		self.text_field.setPlaceholderText("Type to filter")
		self.list = VenueList(self, venues)

		self.text_field.textChanged.connect(self.filter)

		layout.addWidget(self.text_field)
		layout.addWidget(self.list)


	def filter(self, text):
		self.list.filter(text)

	def setVenues(self, venues):
		self.list.setVenues(venues)

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

		if u'address' in venue[u'location']:
			address = venue[u'location'][u'address']
		else:
			address = ""

		if u'crossStreet' in venue[u'location']:
			if address != "":
				address += ", "
			else:
				address = ""
			address += venue[u'location'][u'crossStreet']

		checkin_button = QPushButton("Check-in")
		#checkin_button.setIcon(QIcon.fromTheme("general_clock"))
		self.connect(checkin_button, SIGNAL("clicked()"), self.checkin)

		layout.addWidget(checkin_button, 0, 0, 1, 3)
		layout.addWidget(QLabel("<b>" + venue[u'name'] + "</b>", self), 1, 0)
		layout.addWidget(QLabel(address, self), 2, 0)
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