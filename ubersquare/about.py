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


from PySide.QtGui import QApplication, QDialog, QWidget, QScrollArea, QGridLayout, QLabel, QVBoxLayout, QImage, QPixmap
from PySide.QtCore import Qt
from custom_widgets import Ruler
import foursquare


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        title = "About UberSquare"
        aboutText = "UberSquare is a foursquare application for maemo, specifically, for the Nokia N900.<p>"
        aboutText += "Please report any bugs you may encounter at the project's <a href=\"https://github.com/hobarrera/UberSquare\">GitHub page</a>."

        bsdLicense = """Copyright (c) 2012 Hugo Osvaldo Barrera <hugo@osvaldobarrera.com.ar>

Permission to use, copy, modify, and distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""
        foursquareDisclaimer = """This application uses the foursquare(r) application programming interface but is not endorsed or certified by Foursquare Labs, Inc.  All of the foursquare(r) logos (including all badges) and trademarks displayed on this application are the property of Foursquare Labs, Inc.
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
        aboutTextLabel.setOpenExternalLinks(True)

        bsdLicenseLabel = QLabel(bsdLicense)
        bsdLicenseLabel.setWordWrap(True)

        foursquareDisclaimerLabel = QLabel(foursquareDisclaimer)
        foursquareDisclaimerLabel.setWordWrap(True)
        i = 0

        gridLayout.addWidget(aboutTextLabel, i, 0)
        i +=1
        gridLayout.addWidget(Ruler(), i, 0)
        i +=1

        gridLayout.addWidget(bsdLicenseLabel, i, 0)
        i +=1
        gridLayout.addWidget(Ruler(), i, 0)
        i +=1

        poweredbyLabel = QLabel()
        poweredbyImage = QImage(foursquare.image("https://playfoursquare.s3.amazonaws.com/press/logo/poweredByFoursquare_gray.png"))
        poweredbyLabel.setPixmap(QPixmap(poweredbyImage))
        gridLayout.addWidget(poweredbyLabel, i, 0, Qt.AlignHCenter)
        i +=1

        gridLayout.addWidget(foursquareDisclaimerLabel, i, 0)