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


from PySide.QtGui import QApplication, QDialog, QWidget, QScrollArea, QGridLayout, QLabel, QFrame, QVBoxLayout


class AboutDialog(QDialog):
	def __init__(self, parent=None):
		super(AboutDialog, self).__init__(parent)
		title = "About UberSquare"
		aboutText = "UberSquare is a foursquare for maemo, specifically, for the Nokia N900.  Be sure to report any bugs you may find, and feel free to email me if you have any suggestions, etc."

		bsdLicense = """
Copyright (c) 2012 Hugo Osvaldo Barrera <hugo@osvaldobarrera.com.ar>

Permission to use, copy, modify, and distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""
		foursquareDisclaimer = """
This application uses the foursquare(r) application programming interface but is not endorsed or certified by Foursquare Labs, Inc.  All of the foursquare(r) logos (including all badges) and trademarks displayed on this application are the property of Foursquare Labs, Inc.
"""

		self.setWindowTitle(title)
		self.centralWidget = QWidget()

		#Main Layout
		layout = QVBoxLayout()
		layout.setSpacing(0)
		self.setLayout(layout)

		#Content Layout
		self.container = QWidget()

		self.scrollArea = QScrollArea()
		self.scrollArea.setWidget(self.container)

		layout.addWidget(self.scrollArea)

		self.scrollArea.setWidgetResizable(True)

		gridLayout = QGridLayout()
		self.container.setLayout(gridLayout)

		aboutTextLabel = QLabel(aboutText)
		aboutTextLabel.setWordWrap(True)

		bsdLicenseLabel = QLabel(bsdLicense)
		bsdLicenseLabel.setWordWrap(True)

		foursquareDisclaimerLabel = QLabel(foursquareDisclaimer)
		foursquareDisclaimerLabel.setWordWrap(True)

		gridLayout.addWidget(aboutTextLabel, 0, 0)
		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setMaximumWidth(QApplication.desktop().screenGeometry().width() * 0.5)
		gridLayout.addWidget(line, 1, 0)

		gridLayout.addWidget(bsdLicenseLabel, 2, 0)
		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setMaximumWidth(QApplication.desktop().screenGeometry().width() * 0.5)
		gridLayout.addWidget(line, 3, 0)

		gridLayout.addWidget(foursquareDisclaimerLabel, 4, 0)
		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setMaximumWidth(QApplication.desktop().screenGeometry().width() * 0.5)
		gridLayout.addWidget(line, 5, 0)

		gridLayout.addWidget(QLabel("TODO: Insert \"powered by foursquare\" image here."), 6, 0)
