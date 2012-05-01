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

#from PySide.QtGui import QDesktopServices
from PySide.QtCore import *
from PySide.QtGui import *
from foursquare import Cache
from locationProviders import LocationProvider
from custom_widgets import CategorySelector, UberSquareWindow, Ruler, Title
from threads import TipMarkTodoBackgroundThread, TipMarkDoneBackgroundThread, LeaveTipThread, VenueDetailsThread
from PySide.QtMaemo5 import *
from checkins import CheckinConfirmation, CheckinDetails

import foursquare


class VenueListModel(QAbstractListModel):
	"""
	The inner model user to contain the list of venues.
	"""
	def __init__(self, venues):
		super(VenueListModel, self).__init__()
		self.venues = venues

	VenueRole = 849561745

	def rowCount(self, role=Qt.DisplayRole):
		if self.venues:
			return len(self.venues)
		else:
			return 0

	def data(self, index, role=Qt.DisplayRole):
		venue = self.venues[index.row()]['venue']
		if role == Qt.DisplayRole:
			name = venue['name']
			if len(name) > 72:
				name = name[0:70]
			address = "(no address)"
			if 'address' in venue['location']:
				address = venue['location']['address']
				if len(address) > 72:
					address = address[0:70]
			distance = ""
			if 'distance' in venue['location']:
				distance = " (" + str(venue['location']['distance']) + " metres away)"
			return name + "\n  " + address + distance
		elif role == Qt.DecorationRole:
			if len(venue['categories']) > 0:
				prefix = venue['categories'][0]['icon']['prefix']
				extension = venue['categories'][0]['icon']['name']
				image_url = prefix + "64" + extension
			else:
				image_url = "https://foursquare.com/img/categories/none_64.png"
			return QIcon(foursquare.image(image_url))
			
		elif role == VenueListModel.VenueRole:
			return venue

	def setVenues(self, venues):
		self.venues = venues
		self.reset()


class VenueList(QListView):
	"""
	The list widget, that actually shows the list of venues
	"""
	def __init__(self, parent, venues):
		super(VenueList, self).__init__(parent)
		self.model = VenueListModel(venues)

		self.proxy = QSortFilterProxyModel(self)
		self.proxy.setSourceModel(self.model)
		self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
		self.setModel(self.proxy)

		self.clicked.connect(self.venue_selected)

	def venue_selected(self, index):
		venue = self.proxy.data(index, VenueListModel.VenueRole)
		cachedVenue = foursquare.venues_venue(venue['id'], foursquare.CacheOnly)
		if not cachedVenue:
			d = VenueDetailsWindow(self, venue, False)
		else:
			d = VenueDetailsWindow(self, cachedVenue, True)
		d.show()

	def filter(self, text):
		self.proxy.setFilterRegExp(text)
		self.proxy.filterRegExp()

	def setVenues(self, venues):
		self.model.setVenues(venues)


class VenueListWindow(UberSquareWindow):
	def __init__(self, title, venues, parent):
		super(VenueListWindow, self).__init__(parent)

		self.setWindowTitle(title)

		self.cw = QWidget(self)
		self.setCentralWidget(self.cw)

		layout = QVBoxLayout(self.cw)

		self.text_field = QLineEdit(self)
		#QPlainTextEdit es multilinea
		self.text_field.setPlaceholderText("Type to filter")
		self.list = VenueList(self, venues)

		self.text_field.textChanged.connect(self.filter)

		layout.addWidget(self.text_field)
		layout.addWidget(self.list)

		updateVenues = Signal()
		self.connect(self, SIGNAL("updateVenues()"), self._updateVenues)

	def _updateVenues(self):
		self.setVenues(self.parent().venues())
		if not self.shown:
			self.show()

	def filter(self, text):
		self.list.filter(text)

	def setVenues(self, venues):
		self.list.setVenues(venues)


class Tip(QWidget):
	def __init__(self, tip, parent=None):
		super(Tip, self).__init__(parent)

		gridLayout = QGridLayout()
		self.setLayout(gridLayout)
		self.tip = tip

		tipLabel = QLabel(tip['text'], self)
		tipLabel.setWordWrap(True)
		gridLayout.addWidget(tipLabel, 0, 0, 2, 1)

		self.done_checkbox = QCheckBox("Done! (" + str(tip['done']['count']) + ")")
		self.done_checkbox.setChecked(self.isTipDone())
		self.done_checkbox.stateChanged.connect(self.markDone)

		self.todo_checkbox = QCheckBox("To-do (" + str(tip['todo']['count']) + ")")
		self.todo_checkbox.setChecked(self.isTipTodo())
		self.todo_checkbox.stateChanged.connect(self.markTodo)

		gridLayout.addWidget(self.done_checkbox, 0, 1, 1, 1)
		gridLayout.addWidget(self.todo_checkbox, 1, 1, 1, 1)
		gridLayout.setColumnStretch(0, 1)

	def isTipInGroupType(self, groupType):
		if 'listed' in self.tip:
			if 'groups' in self.tip['listed']:
				for group in self.tip['listed']['groups']:
					if group['type'] == groupType:
						return True
		return False

	def isTipDone(self):
		return self.isTipInGroupType("dones")

	def isTipTodo(self):
		return self.isTipInGroupType("todos")

	def markTodo(self, state):
		TipMarkTodoBackgroundThread(self.tip['id'], self.todo_checkbox.isChecked(), self).start()

	def markDone(self, state):
		TipMarkDoneBackgroundThread(self.tip['id'], self.done_checkbox.isChecked(), self).start()


class NewTipWidget(QWidget):
	def __init__(self, venueId, parent=None):
		super(NewTipWidget, self).__init__(parent)
		self.__parent = parent

		gridLayout = QGridLayout()
		self.setLayout(gridLayout)
		self.venueId = venueId

		self.tip_text = QLineEdit()
		self.tip_text.setPlaceholderText("Write something and then...")
		gridLayout.addWidget(self.tip_text, 0, 0)

		self.tip_button = QPushButton("Leave tip!")
		self.tip_button.clicked.connect(self.addTip)
		gridLayout.addWidget(self.tip_button, 0, 1)

	def addTip(self):
		t = LeaveTipThread(self.venueId, self.tip_text.text(), self.__parent)
		t.start()
		self.__parent.showWaitingDialog.emit()


class VenueDetailsWindow(UberSquareWindow):
	def __init__(self, parent, venue, fullDetails):
		super(VenueDetailsWindow, self).__init__(parent)
		self.venue = venue

		self.fullDetails = fullDetails

		self.setWindowTitle(venue['name'])

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

		# name
		name = venue['name']
		if len(venue['categories']) > 0:
			name += " (" + venue['categories'][0]['name'] + ")"

		# address
		address = ""
		if 'address' in venue['location']:
			address = venue['location']['address']

		if 'crossStreet' in venue['location']:
			if address != "":
				address += ", "
			address += venue['location']['crossStreet']

		# address2
		address2 = ""
		if 'postalCode' in venue['location']:
			address2 = venue['location']['postalCode']

		if 'city' in venue['location']:
			if address2 != "":
				address2 += ", "
			address2 += venue['location']['city']

		# times
		if 'beenHere' in venue:
			if not fullDetails:
				count = venue['beenHere']
			else:
				count = venue['beenHere']['count']
			times = "<b>Yo've been here "
			if count == 1:
				times += "once"
			else:
				times += str(count) + " times"
			times += "</b>"
		else:
			times = "<b>Yo've never been here</b>"

		checkin_button = QPushButton("Check-in")
		self.connect(checkin_button, SIGNAL("clicked()"), self.checkin)

		i = 0
		gridLayout.addWidget(checkin_button, i, 1)
		self.shout_text = QLineEdit(self)
		self.shout_text.setPlaceholderText("Shout something")
		gridLayout.addWidget(self.shout_text, i, 0)
		i += 1
		gridLayout.addWidget(Title(name, self), i, 0, 1, 2)
		i += 1
		gridLayout.addWidget(QLabel(address, self), i, 0, 1, 2)
		i += 1
		gridLayout.addWidget(QLabel(address2, self), i, 0, 1, 2)
		for item in venue['categories']:
			if 'primary' in item and item['primary'] == "true":
				i += 1
				gridLayout.addWidget(QLabel(item['name'], self), i, 0, 1, 2)
		i += 1
		gridLayout.addWidget(Ruler(), i, 0, 1, 2)

		if 'description' in venue:
			i += 1
			description_label = QLabel(venue['description'])
			description_label.setWordWrap(True)
			gridLayout.addWidget(description_label, i, 0, 1, 2)
			i += 1
			gridLayout.addWidget(Ruler(), i, 0, 1, 2)

		i += 1
		gridLayout.addWidget(QLabel(times, self), i, 0)
		i += 1
		gridLayout.addWidget(QLabel("Total Checkins: " + str(venue['stats']['checkinsCount']), self), i, 0)
		i += 1
		gridLayout.addWidget(QLabel("Total Visitors: " + str(venue['stats']['usersCount']), self), i, 0)

		if 'hereNow' in venue:
			hereNow = venue['hereNow']['count']
			if hereNow == 0:
				hereNow = "There's no one here now."
			elif hereNow == 1:
				hereNow = "There's just one person here now."
			else:
				hereNow = "There are " + repr(hereNow) + " people here now."
			i += 1
			gridLayout.addWidget(QLabel(hereNow, self), i, 0)

		if 'phone' in venue['contact']:
			i += 1
			phoneCallButton = QPushButton("Call (" + venue['contact']['formattedPhone'] + ")")
			phoneCallButton.setIcon(QIcon.fromTheme("general_call"))
			self.connect(phoneCallButton, SIGNAL("clicked()"), self.startPhoneCall)
			gridLayout.addWidget(phoneCallButton, i, 0, 1, 2)

		if 'url' in venue:
			i += 1
			websiteButton = QPushButton("Visit Website")
			websiteButton.setIcon(QIcon.fromTheme("general_web"))
			self.connect(websiteButton, SIGNAL("clicked()"), self.openUrl)
			gridLayout.addWidget(websiteButton, i, 0, 1, 2)

		if 'mayor' in venue:
			if 'user' in venue['mayor']:
				mayorName = venue['mayor']['user']['firstName']
				mayorCount = venue['mayor']['count']
				mayorText = mayorName + " is the mayor with " + str(mayorCount) + " checkins!"
				mayorButton = QPushButton()
				mayorButton.setText(mayorText)
				mayorButton.setIcon(QIcon(foursquare.image(venue['mayor']['user']['photo'])))
			else:
				mayorButton = QLabel("This venue has no mayor")
			i += 1
			gridLayout.addWidget(mayorButton, i, 0, 1, 2)

		# TODO: menu
		# TODO: specials

		if 'tips' in venue:
			i += 1
			if venue['tips']['count'] == 0:
				gridLayout.addWidget(QLabel("<b>There isn't a single tip!</b>", self), i, 0)
			else:
				if venue['tips']['count'] == 1:
					gridLayout.addWidget(QLabel("<b>Just one tip</b>", self), i, 0)
				else:
					gridLayout.addWidget(QLabel("<b>" + str(venue['tips']['count']) + " tips</b>", self), i, 0)
				for group in venue['tips']['groups']:
					for tip in group['items']:
						i += 1
						gridLayout.addWidget(Tip(tip), i, 0, 1, 2)
						i += 1
						line = QFrame()
						line.setFrameShape(QFrame.HLine)
						line.setMaximumWidth(QApplication.desktop().screenGeometry().width() * 0.5)
						gridLayout.addWidget(line, i, 0, 1, 2)

			i += 1
			gridLayout.addWidget(NewTipWidget(venue['id'], self), i, 0, 1, 2)

		if not fullDetails:
			info_button_label = "Fetch full details"
		else:
			info_button_label = "Refresh venue details"
		more_info_button = QPushButton(info_button_label)
		more_info_button.setIcon(QIcon.fromTheme("general_refresh"))
		self.connect(more_info_button, SIGNAL("clicked()"), self.more_info)

		i += 1
		gridLayout.addWidget(more_info_button, i, 0, 1, 2)

		showMoreInfo = Signal()
		self.connect(self, SIGNAL("showMoreInfo()"), self.more_info)

	def startPhoneCall(self):
		QDesktopServices.openUrl("tel:" + self.venue['contact']['phone'])

	def openUrl(self):
		QDesktopServices.openUrl(self.venue['url'])

	def __showWaitingDialog(self):
		self.waitDialog.exec_()

	def __hideWaitingDialog(self):
		self.waitDialog.hide()

	def more_info(self):
		if not self.fullDetails:
			venue = foursquare.venues_venue(self.venue['id'], Cache.CacheOrNull)
			if venue:
				self.close()
				VenueDetailsWindow(self.parent(), venue, True).show()
				return
		# FIXME!
		self.fullDetails = False
		VenueDetailsThread(self.venue['id'], self).start()
		self.__showWaitingDialog()

	def checkin(self):
		c = CheckinConfirmation(self, self.venue)
		c.exec_()
		if c.result() == QDialog.Accepted:
			try:
				# TODO: do this in a separate thread
				ll = LocationProvider().get_ll(self.venue)
				response = foursquare.checkin(self.venue, ll, self.shout_text.text(), c.broadcast())
				CheckinDetails(self, response).show()
			except IOError:
				self.networkError.emit()


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

		i = 0
		self.name = QLineEdit(self)
		self.name.setPlaceholderText("Name")
		gridLayout.addWidget(self.name, i, 0, 1, 2)

		i += 1
		self.address = QLineEdit(self)
		self.address.setPlaceholderText("Address")
		gridLayout.addWidget(self.address, i, 0)
		self.crossStreet = QLineEdit(self)
		self.crossStreet.setPlaceholderText("Cross Address")
		gridLayout.addWidget(self.crossStreet, i, 1)

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
		self.category = CategorySelector(self)
		gridLayout.addWidget(self.category, i, 0, 2, 2)
		i += 1

		i += 1
		self.ll = QLineEdit(self)
		self.ll.setPlaceholderText("Coordinates")
		self.ll.setText(ll)
		gridLayout.addWidget(QLabel("Latitude/Longitude: "), i, 0)
		gridLayout.addWidget(self.ll, i, 1)

		i += 1
		self.add_venue_button = QPushButton("Add Venue")
		self.connect(self.add_venue_button, SIGNAL("clicked()"), self.add_venue)
		gridLayout.addWidget(self.add_venue_button, i, 0, 1, 2)

	def category_selected(self, index):
		if index != -1:
			subcategories = self.category.pickSelector().model().get_data(index)['categories']
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
		venue['crossStreet'] = self.crossStreet.text()
		venue['city'] = self.city.text()
		venue['state'] = self.state.text()
		venue['zip'] = self.zip.text()
		venue['phone'] = self.phone.text()
		venue['twitter'] = self.twitter.text()
		venue['primaryCategoryId'] = self.category.selectedCategory()
		venue['description'] = self.description.text()
		venue['url'] = self.url.text()
		venue['ignoreDuplicates'] = self.venue['ignoreDuplicates']
		self.venue['ignoreDuplicates'] = "false"
		if 'ignoreDuplicatesKey' in self.venue:
			venue['ignoreDuplicatesKey'] = self.venue['ignoreDuplicatesKey']

		response = foursquare.venue_add(venue)

		if response['meta']['code'] == 409:
			title = "Duplicate detected"

			venues = dict()
			i = 0
			for venue in response['response']['candidateDuplicateVenues']:
				venues[i] = dict()
				venues[i]['venue'] = venue
				i += 1

			msgBox = QMessageBox(self)
			msgBox.setText("Foursquare says this venue looks like a duplicate.<br> Make sure it isn't; if it is, then click \"Add Venue\" again.")
			msgBox.setWindowTitle(title)
			msgBox.exec_()

			self.venue['ignoreDuplicates'] = "true"
			self.venue['ignoreDuplicatesKey'] = response['response']['ignoreDuplicatesKey']

			w = VenueListWindow("Posible matches", venues, self)
			w.show()
		else:
			msgBox = QMessageBox(self)
			msgBox.setText("Venue successfully created")
			msgBox.setWindowTitle("Venue added")
			msgBox.exec_()

			v = VenueDetailsWindow(self, response['response']['venue'], True)
			v.show()
