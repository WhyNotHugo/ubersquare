import sys
#from PySide import QtCore, QtGui
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtMaemo5 import *

from foursquare import *
from checkin import *


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

		#self.setDetailedText(json.dumps(venue).replace("\n","<br>"))

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

		l = QLabel(text)

		vbox = QVBoxLayout()
		vbox.addWidget(l)
 	
		b = QPushButton("Ok")
		self.connect(b, SIGNAL("clicked()"), self.close)
 
		vbox.addWidget(b)
		self.setLayout(vbox)

class VenueModel(QAbstractListModel):
	def __init__(self):
		super(VenueModel, self).__init__()
		self.venues = get_history()

	def rowCount(self, role=Qt.DisplayRole):
		return len(self.venues)

	def data(self, index, role=Qt.DisplayRole):
		if role == Qt.DisplayRole:
			venue = self.venues[index.row()][u'venue']
			if u'address' in venue[u'location']:
				return venue[u'name'] + "\n" + venue[u'location'][u'address']
			else:
				return venue[u'name']

	def get_venue(self, index):
		return self.venues[index.row()][u'venue']

v = True

class MainWindow(QWidget):

	def __init__(self):
		super(MainWindow, self).__init__(None)

		menubar = QMenuBar(self)
		menu_File = QMenu(menubar)
		self.setWindowTitle("UberSquare")

		vbox = QVBoxLayout()
		
		checkin_button = QPushButton("Check in...")

		self.connect(checkin_button, SIGNAL("clicked()"), self.checkin_button_pushed)

		# my_list = QListWidget()
		# my_list.addItem("<b>hola!</b>\nadfsafads")
		# my_list.setSortingEnabled(True)

		second_list = QListView(self)
		self.model = VenueModel()
		second_list.setModel(self.model)
		second_list.clicked.connect(self.venue_selected)


		vbox.addWidget(checkin_button)
		# vbox.addWidget(my_list)
		vbox.addWidget(second_list)


		self.setLayout(vbox)
		#selector = QMaemo5ListPickSelector(self)
		#selector.show()

		# self.ibox = QMaemo5InformationBox()
		# self.ibox.information(self, "This message will freeze the screen", 3000)

	def venue_selected(self, index):
		venue = self.model.get_venue(index)
		c = CheckinConfirmation(self, venue)
		c.exec_()
		if c.buttonRole(c.clickedButton()) == QMessageBox.YesRole:
			ll = get_aproximate_location(venue)
			response = checkin(venue, ll)
			CheckinDetails(self, response).show()

	def checkin_button_pushed(self):
		d = QDialog(self)
		d.setWindowTitle("Hola!")
		vbox = QVBoxLayout()
		l = QLabel("Esto es tipo probando. No se si poner la lista en un dialog, u\n otra window. Esto se hace multiline solo?")
		vbox.addWidget(l)
		b = QPushButton("Close window")
		self.connect(b, SIGNAL("clicked()"), d.close)
		vbox.addWidget(b)
		d.setLayout(vbox)
		d.show()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.show()
 
	sys.exit(app.exec_())