from PySide.QtCore import *
from PySide.QtGui import *
import sys
from foursquare import *
import foursquare

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

		message = ""
		score = ""
		mayorship = ""
		badge = ""

		for item in checking_details[u'notifications']:
			if item[u'type'] == "message":
				message += item[u'item'][u'message'] + "<p>"
			elif item[u'type'] == "score":
				score += "Total points: %d" % item[u'item'][u'total']
				for scoreItem in item[u'item'][u'scores']:
					score += "<br>+%(points)d   %(message)s" % \
					{'points': scoreItem[u'points'], 'message' : scoreItem[u'message']}
				score += "<p>"
			elif item[u'type'] == "mayorship":
				mayorship = item[u'item'][u'message']
			elif item[u'type'] == "badge":
				badge = "<p>" + item[u'item'][u'message']

		text = message + score + mayorship + badge

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
		venue = self.venues[index.row()][u'venue']
		if role == Qt.DisplayRole:
			if u'address' in venue[u'location']:
				return venue[u'name'] + "\n  " + venue[u'location'][u'address']
			else:
				return venue[u'name']
		elif role == Qt.DecorationRole:
			if len(venue[u'categories']) > 0:
				prefix = venue[u'categories'][0][u'icon'][u'prefix']
				extension = venue[u'categories'][0][u'icon'][u'name']
				return QIcon(foursquare.image(prefix + "64" + extension))
		elif role == VenueModel.VenueRole:
			return venue

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

class VenueListWindow(QMainWindow):
	def __init__(self, parent, title, venues):
		super(VenueListWindow, self).__init__(parent)
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
	def __init__(self, parent, venue, full = False):
		super(VenueDetailsWindow, self).__init__(parent)
		if maemo:
			self.setAttribute(Qt.WA_Maemo5StackedWindow)
		self.venue = venue

		self.setWindowTitle(venue[u'name'])

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

		address = ""
		address2 = ""

		if u'address' in venue[u'location']:
			address = venue[u'location'][u'address']

		if u'crossStreet' in venue[u'location']:
			if address != "":
				address += ", "
			address += venue[u'location'][u'crossStreet']

		if u'postalCode' in venue[u'location']:
			address2 = venue[u'location'][u'postalCode']

		if u'city' in venue[u'location']:
			if address2 != "":
				address2 += ", "
			address2 += venue[u'location'][u'city']

		checkin_button = QPushButton("Check-in")
		#checkin_button.setIcon(QIcon.fromTheme("general_clock"))
		self.connect(checkin_button, SIGNAL("clicked()"), self.checkin)

		name = "<b>" + venue[u'name'] + "</b>"
		name += " (" + venue[u'categories'][0][u'name'] + ")"

		i = 0
		gridLayout.addWidget(checkin_button, i, 0, 1, 3)
		i += 1
		self.shout_text = QLineEdit(self)
		self.shout_text.setPlaceholderText("Shout")
		gridLayout.addWidget(self.shout_text, i, 0, 1, 3)
		i += 1
		gridLayout.addWidget(QLabel(name, self), i, 0)
		i += 1
		gridLayout.addWidget(QLabel(address, self), i, 0)
		i += 1
		gridLayout.addWidget(QLabel(address2, self), i, 0)
		for item in venue[u'categories']:
			if item[u'primary'] == "true":
				i += 1
				gridLayout.addWidget(QLabel(item[u'name'], self), i, 0)
		i += 1
		gridLayout.addWidget(QLabel("Total Checkins: " + str(venue[u'stats'][u'checkinsCount']), self), i, 0)
		i += 1
		gridLayout.addWidget(QLabel("Total Users: " + str(venue[u'stats'][u'usersCount']), self), i, 0)
		if u'beenHere' in venue:
			if venue[u'beenHere'] == 1:
				times = "once"
			else:
				times = str(venue[u'beenHere']) +" times"
			i += 1
			gridLayout.addWidget(QLabel("You've been here " + times, self), i, 0)

		full_venue_button = QPushButton("More... (TODO)")
		#checkin_button.setIcon(QIcon.fromTheme("general_clock"))
		#self.connect(checkin_button, SIGNAL("clicked()"), self.checkin)

		i += 1
		gridLayout.addWidget(full_venue_button, i, 0, 1, 3)

	def checkin(self):
		c = CheckinConfirmation(self, self.venue)
		c.exec_()
		if c.buttonRole(c.clickedButton()) == QMessageBox.YesRole:
			try:
				ll = foursquare.get_aproximate_location(self.venue)
				response = checkin(self.venue, ll, self.shout_text.text())
				CheckinDetails(self, response).show()
			except IOError:
	 			self.ibox = QMaemo5InformationBox()
	 			self.ibox.information(self, "Network error; check-in failed. Please try again.", 15000)

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
		if role == CategoryModel.CategoryRole:
			return self.categories[index.row()]
		if role == CategoryModel.SubCategoriesRole:
			return self.categories[index.row()][u'categories']

	def get_data(self, index):
		return self.categories[index]

class CategorySelector(QMaemo5ListPickSelector):
	def __init__(self, categories):
		super(CategorySelector, self).__init__()
		self.setModel(CategoryModel(categories))

class EventEmittingValueButton(QMaemo5ValueButton):
	def __init__(self, text, callback, parent):
		super(EventEmittingValueButton, self).__init__(text, parent)
		self.callback = callback

	def setValueText(self, text):
		super(EventEmittingValueButton, self).setValueText(text)
		self.callback(self.pickSelector().currentIndex())

class NewVenueWindow(QMainWindow):
	def __init__(self, parent, categories, ll):
		super(NewVenueWindow, self).__init__(parent)
		self.setAttribute(Qt.WA_Maemo5StackedWindow)
		self.venue = dict()
		self.venue['ignoreDuplicates'] = "false"

		self.setWindowTitle("New Venue")

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

		#self.connect(checkin_button, SIGNAL("clicked()"), self.checkin)

		i = 0
		self.name = QLineEdit(self)
		self.name.setPlaceholderText("Name")
		gridLayout.addWidget(self.name, i, 0, 1, 2)

		i += 1
		self.address = QLineEdit(self)
		self.address.setPlaceholderText("Address")
		gridLayout.addWidget(self.address, i, 0)
		self.crossAddress = QLineEdit(self)
		self.crossAddress.setPlaceholderText("Cross Address")
		gridLayout.addWidget(self.crossAddress, i, 1)

		i += 1
		self.city = QLineEdit(self)
		self.city.setPlaceholderText("City")
		gridLayout.addWidget(self.city, i, 0)
		self.state = QLineEdit(self)
		self.state.setPlaceholderText("State")
		gridLayout.addWidget(self.state, i, 1)
		
		i += 1
		self.zip = QLineEdit(self)
		self.zip.setPlaceholderText("Zip")
		gridLayout.addWidget(self.zip, i, 0)
		self.phone = QLineEdit(self)
		self.phone.setPlaceholderText("Phone")
		gridLayout.addWidget(self.phone, i, 1)
		
		i += 1
		self.twitter = QLineEdit(self)
		self.twitter.setPlaceholderText("Twitter")
		gridLayout.addWidget(self.twitter, i, 0)
		self.url = QLineEdit(self)
		self.url.setPlaceholderText("URL")
		gridLayout.addWidget(self.url, i, 1)

		i += 1
		self.description = QLineEdit(self)
		self.description.setPlaceholderText("Description")
		gridLayout.addWidget(self.description, i, 0, 1, 2)

		i += 1
		self.category = EventEmittingValueButton("Category", self.category_selected, self)
		gridLayout.addWidget(self.category, i, 0, 1, 2)
		self.category.setPickSelector(CategorySelector(categories))
		self.category.setValueLayout(QMaemo5ValueButton.ValueBesideText)

		i += 1
		self.subcategory = QMaemo5ValueButton("Subcategory", self)
		gridLayout.addWidget(self.subcategory, i, 0, 1, 2)
		self.subcategory.setValueLayout(QMaemo5ValueButton.ValueBesideText)
		
		i += 1
		self.ll = QLineEdit(self)
		self.ll.setPlaceholderText("Coordinates")
		self.ll.setText(ll)
		gridLayout.addWidget(QLabel("Latitude/Longitude: "), i, 0)
		gridLayout.addWidget(self.ll, i, 1)

		i += 1
		self.add_venue_button = QPushButton("Add Venue")
		self.connect(self.add_venue_button, SIGNAL("clicked()"), self.add_venue)
		gridLayout.addWidget(self.add_venue_button, i, 0, 1 ,2)
		
	def category_selected(self, index):
		if index != -1:
			subcategories = self.category.pickSelector().model().get_data(index)[u'categories']
			self.subcategory.setPickSelector(CategorySelector(subcategories))

	def add_venue(self):
		if self.name.text() == "":
			self.ibox = QMaemo5InformationBox()
			self.ibox.information(self, "No name has been specified for this venue.", 2000)
		if self.ll.text() == "":
			self.ibox = QMaemo5InformationBox()
			self.ibox.information(self, "No ll has been specified for this venue.", 2000)

		venue = dict()
		venue['name'] = self.name.text()
		venue['ll'] = self.ll.text()
		venue['address'] = self.address.text()
		venue['crossAddress'] = self.crossAddress.text()
		venue['city'] = self.city.text()
		venue['state'] = self.state.text()
		venue['zip'] = self.zip.text()
		venue['phone'] = self.phone.text()
		venue['twitter'] = self.twitter.text()
		venue['primaryCategoryId'] = self.subcategory.pickSelector().model().get_data(self.subcategory.pickSelector().currentIndex())[u'id']
		venue['description'] = self.description.text()
		venue['url'] = self.url.text()
		venue['ignoreDuplicates'] = self.venue['ignoreDuplicates']
		self.venue['ignoreDuplicates'] = "false"
		if 'ignoreDuplicatesKey' in self.venue:
			venue['ignoreDuplicatesKey'] = self.venue['ignoreDuplicatesKey']


		response = foursquare.venue_add(venue)

		if response[u'meta'][u'code'] == 409:
			title = "Duplicate detected"
	
			venues = dict()
			i = 0
			for venue in response[u'response'][u'candidateDuplicateVenues']:
				venues[i] = dict()
				venues[i][u'venue'] = venue
				i +=  1

			msgBox = QMessageBox(self)
			msgBox.setText("Foursquare says this venue looks like a duplicate.<br> Make sure it isn't; if it is, then click \"Add Venue\" again.")
			msgBox.setWindowTitle(title)
			msgBox.exec_()

			self.venue['ignoreDuplicates'] = "true"
			self.venue['ignoreDuplicatesKey'] = response[u'response'][u'ignoreDuplicatesKey']

			w = VenueListWindow(self, "Posible matches", venues)
			w.show()
		else:
			msgBox = QMessageBox(self)
			msgBox.setText("Venue successfully created")
			msgBox.setWindowTitle("Venue added")
			msgBox.exec_()

			v = VenueDetailsWindow(self, response[u'response'][u'venue'])
			v.show()