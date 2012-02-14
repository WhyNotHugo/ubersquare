import sys
#from PySide import QtCore, QtGui
from PySide.QtCore import *
from PySide.QtGui import *
try:
	from PySide.QtMaemo5 import *
except ImportError:
	print "Couldn't import QtMaemo5. You're probably not running on maemo."
	print "I'll probably crash at some point, though some stuff will work."

from foursquare import *
#from checkin import *


def sayHello():
	print "Hello World!"

#QDialog

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
	def __init__(self, parent, venues):
		super(VenueList,self).__init__(parent)
		self.model = VenueModel(venues)
		self.setModel(self.model)
		self.clicked.connect(self.venue_selected)

	def venue_selected(self, index):
		venue = self.model.get_venue(index)
		c = CheckinConfirmation(self, venue)
		c.exec_()
		if c.buttonRole(c.clickedButton()) == QMessageBox.YesRole:
			ll = get_aproximate_location(venue)
			response = checkin(venue, ll)
			CheckinDetails(self, response).show()
		

class HistoryWindow(QMainWindow):
	def __init__(self, parent):
		super(HistoryWindow, self).__init__(parent)
		self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.setWindowTitle("Previous Venues")

		self.cw = VenueList(self, get_history())
		self.setCentralWidget(self.cw)

class TodoWindow(QMainWindow):
	def __init__(self, parent):
		super(TodoWindow, self).__init__(parent)
		self.setAttribute(Qt.WA_Maemo5StackedWindow)

		self.setWindowTitle("Todo Venues")

		self.cw = VenueList(self, get_todo_venues())
		self.setCentralWidget(self.cw)

class MainWindow(QMainWindow):

	def __init__(self):
		super(MainWindow, self).__init__(None)
		self.setAttribute(Qt.WA_Maemo5StackedWindow)

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

		vbox.addWidget(previous_venues_button)
		vbox.addWidget(todo_venues_button)
		vbox.addStretch()

		#44self.setLayout(vbox)
		#selector = QMaemo5ListPickSelector(self)
		#selector.show()

		# self.ibox = QMaemo5InformationBox()
		# self.ibox.information(self, "This message will freeze the screen", 3000)

	def previous_venues_pushed(self):
		# d = QDialog(self)
		# d.setWindowTitle("Hola!")
		# vbox = QVBoxLayout()
		# l = QLabel("Esto es tipo probando. No se si poner la lista en un dialog, u\n otra window. Esto se hace multiline solo?")
		# vbox.addWidget(l)
		# b = QPushButton("Close window")
		# self.connect(b, SIGNAL("clicked()"), d.close)
		# vbox.addWidget(b)
		# d.setLayout(vbox)
		# d.show()
		a = HistoryWindow(self)
		a.show()

	def todo_venues_pushed(self):
		a = TodoWindow(self)
		a.show()
		


if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.show()
 
	sys.exit(app.exec_())