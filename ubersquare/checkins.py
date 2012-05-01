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

from PySide.QtGui import QDialog, QLabel, QPushButton, QVBoxLayout, QMessageBox, QWidget, QGridLayout, QCheckBox
from PySide.QtCore import SIGNAL
import foursquare
try:
    import json
except ImportError:
    import simplejson as json


class CheckinConfirmation(QDialog):
    def __init__(self, parent, venue):
        super(CheckinConfirmation, self).__init__(parent)
        self.setWindowTitle("Checkin")
        self.centralWidget = QWidget()

        #Main Layout
        layout = QGridLayout()
        #layout.setSpacing(0)
        self.setLayout(layout)


        text = "You're checking in @<b>" + venue['name'] + "</b>"
        if 'address' in venue['location']:
            text += ", " + venue['location']['address']
        text += "."
        textLabel = QLabel(text, self)
        textLabel.setWordWrap(True)

        okButton = QPushButton("Ok")
        self.connect(okButton, SIGNAL("clicked()"), self.accept)
        cancelButton = QPushButton("Cancel")
        self.connect(cancelButton, SIGNAL("clicked()"), self.reject)

        # TODO: make this a separate widget
        #----
        self.tw = QCheckBox("Twitter")
        self.fb = QCheckBox("Facebook")

        broadcast = foursquare.config_get("broadcast")
        if broadcast:
            if not ", " in broadcast:
                self.tw.setChecked("twitter" in broadcast)
                self.fb.setChecked("facebook" in broadcast)
        #----

        layout.addWidget(textLabel, 0, 0, 1, 2)
        layout.addWidget(self.tw, 1, 0)
        layout.addWidget(self.fb, 1, 1)
        layout.addWidget(okButton, 1, 2)
        #layout.addWidget(cancelButton, 1, 1)
    def broadcast(self):
        broadcast = "public"
        if self.tw.isChecked():
            broadcast += ",twitter"
        if self.fb.isChecked():
            broadcast += ",facebook"

        
class CheckinDetails(QDialog):
    def __init__(self, parent, checking_details):
        super(CheckinDetails, self).__init__(parent)
        self.checking_details = checking_details
        self.setWindowTitle("Check-in successful")

        message = ""
        score = ""
        mayorship = ""
        badge = ""

        for item in checking_details['notifications']:
            if item['type'] == "message":
                message += item['item']['message'] + "<p>"
            elif item['type'] == "score":
                score += "Total points: %d" % item['item']['total']
                for scoreItem in item['item']['scores']:
                    score += "<br>+%(points)d   %(message)s" % \
                    {'points': scoreItem['points'], 'message': scoreItem['message']}
                score += "<p>"
            elif item['type'] == "mayorship":
                mayorship = item['item']['message']
            elif item['type'] == "badge":
                print json.dumps(item['item'], sort_keys=True, indent=4)
                badge = "You got the \"" + item['item']['name'] + "\" badge!"

        text = message + score + mayorship + badge

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(text))

        ok_button = QPushButton("Ok")
        self.connect(ok_button, SIGNAL("clicked()"), self.close)

        vbox.addWidget(ok_button)
        self.setLayout(vbox)
