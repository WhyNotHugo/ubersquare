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

from PySide.QtGui import QDialog, QLabel, QPushButton, QVBoxLayout
from PySide.QtCore import Signal, SIGNAL

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