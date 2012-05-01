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

import sys
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtGui import QCheckBox

from PySide.QtMaemo5 import QMaemo5ValueButton, QMaemo5InformationBox

import foursquare
import foursquare_auth
from venues import NewVenueWindow, VenueListWindow
from foursquare import Cache
from locationProviders import LocationProviderSelector, LocationProvider
from threads import VenueProviderThread, UserUpdaterThread, ImageCacheThread, UpdateSelf, VenueSearchThread
from custom_widgets import SignalEmittingValueButton, CategorySelector, UberSquareWindow, Title, Ruler
from users import UserListWindow
from about import AboutDialog
from datetime import datetime

class Profile(QWidget):
    def __init__(self, parent=None):
        super(Profile, self).__init__(parent)
        self.user = foursquare.get_user("self", foursquare.CacheOrGet)['user']
        self.photo_label = QLabel()

        self.textLabel = QLabel()
        self.textLabel.setWordWrap(True)
        self.__updateInfo(True)

        name = ""
        if 'firstName' in self.user:
            name += self.user['firstName'] + " "
        if 'lastName' in self.user:
            name += self.user['lastName']

        self.nameTitle = Title(name)

        profileLayout = QGridLayout()
        self.setLayout(profileLayout)
        profileLayout.addWidget(self.photo_label, 0, 0, 2, 1)
        profileLayout.addWidget(self.nameTitle, 0, 1)
        profileLayout.addWidget(self.textLabel, 1, 1)
        profileLayout.setColumnStretch(1, 5)
        profileLayout.setSpacing(5)
        profileLayout.setContentsMargins(11, 11, 11, 11)

        clicked = Signal()
        self.connect(self, SIGNAL("clicked()"), self.__clicked)

        selfUpdated = Signal()
        self.connect(self, SIGNAL("selfUpdated()"), self.__updateInfo)

        foursquare.add_checkin_hook(self.checkin)

    def __clicked(self):
        t = UpdateSelf(self)
        t.start()
        QMaemo5InformationBox.information(self, "Updating stats...", 1500)

    def mousePressEvent(self, event):
        self.clicked.emit()

    def checkin(self):
        t = UpdateSelf(self)
        t.start()

    def __updateInfo(self, initial=False):
        if not initial:
            QMaemo5InformationBox.information(self, "Stats updated!", 1500)
            self.user = foursquare.get_user("self", foursquare.CacheOrGet)['user']

        badges = "<b>" + str(self.user['badges']['count']) + "</b> badges"
        mayorships = "<b>" + str(self.user['mayorships']['count']) + "</b> mayorships"
        checkins = "<b>" + str(self.user['checkins']['count']) + "</b> checkins"

        if 'items' in self.user['checkins']:
            location = self.user['checkins']['items'][0]['venue']['name']
            lastSeen = self.user['checkins']['items'][0]['createdAt']
            lastSeen = datetime.fromtimestamp(lastSeen).strftime("%Y-%m-%d %X")
            location = "Last seen @" +  location # + "</b>, at <i>" + lastSeen + "</i>"
        else:
            location = "Never checked in anywhere!"


        text = location + "<br>" + badges + " | " + mayorships + " | " + checkins
        self.textLabel.setText(text)

        self.photo = QImage(foursquare.image(self.user['photo']))
        self.photo_label.setPixmap(QPixmap(self.photo))


class MainWindow(UberSquareWindow):
    def __init__(self):
        super(MainWindow, self).__init__(None)
        self.setWindowTitle("UberSquare")

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

        previous_venues_button = QPushButton("Visited")
        previous_venues_button.setIcon(QIcon.fromTheme("general_clock"))
        self.connect(previous_venues_button, SIGNAL("clicked()"), self.previous_venues_pushed)

        todo_venues_button = QPushButton("To-Do List")
        todo_venues_button.setIcon(QIcon.fromTheme("calendar_todo"))
        self.connect(todo_venues_button, SIGNAL("clicked()"), self.todo_venues_pushed)

        search_venues_button = QPushButton("Search/Explore")
        self.connect(search_venues_button, SIGNAL("clicked()"), self.search_venues_pushed)

        self.location_button = SignalEmittingValueButton("Location", self.locationSelected, self)
        self.location_button.setPickSelector(LocationProviderSelector())
        self.location_button.setValueLayout(QMaemo5ValueButton.ValueUnderTextCentered)

        images_button = QPushButton("Update image cache")
        self.connect(images_button, SIGNAL("clicked()"), self.imageCache_pushed)

        logout_button = QPushButton("Forget credentials")
        self.connect(logout_button, SIGNAL("clicked()"), self.logout_pushed)

        new_venue_button = QPushButton("Create Venue")
        self.connect(new_venue_button, SIGNAL("clicked()"), self.new_venue_pushed)

        leaderboard_button = QPushButton("Leaderboard")
        self.connect(leaderboard_button, SIGNAL("clicked()"), self.leaderboard_button_pushed)

        settings_button = QPushButton("Sharing")
        self.connect(settings_button, SIGNAL("clicked()"), self.settings_button_pushed)

        row = 0
        gridLayout.addWidget(Profile(), row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(previous_venues_button, row, 0)
        gridLayout.addWidget(todo_venues_button, row, 1)
        row += 1
        gridLayout.addWidget(new_venue_button, row, 0)
        gridLayout.addWidget(search_venues_button, row, 1)
        row += 1
        gridLayout.addWidget(leaderboard_button, row, 0)
        row += 1
        gridLayout.addWidget(QLabel("<b>Settings</b>"), row, 0, 1, 2, Qt.AlignHCenter)
        row += 1
        gridLayout.addWidget(self.location_button, row, 0)
        gridLayout.addWidget(settings_button, row, 1)
        row += 1
        gridLayout.addWidget(images_button, row, 0)
        gridLayout.addWidget(logout_button, row, 1)

        self.setupMenu()
        self._venues = None

        showSearchResults = Signal()
        self.connect(self, SIGNAL("showSearchResults()"), self.__showSearchResults)

    def imageCache_pushed(self):
        c = QMessageBox(self)
        c.setWindowTitle("Update image cache?")
        c.setText("This will update all the category images in the cache. Make sure you have a good connection, and don't have to pay-by-megabyte")
        c.addButton("Yes", QMessageBox.YesRole)
        c.addButton("No", QMessageBox.NoRole)
        c.setIcon(QMessageBox.Question)
        c.exec_()
        if c.buttonRole(c.clickedButton()) == QMessageBox.YesRole:
            t = ImageCacheThread(self)
            t.start()
            self.waitDialog = QMessageBox(self)
            self.waitDialog.setWindowTitle("Please wait...")
            self.waitDialog.setText("This dialog will auto-close once downloading finishes.")
            self.waitDialog.exec_()

    def __showSearchResults(self):
        self.progressDialog().close()

    def setupMenu(self):
        about = QAction(self)
        about.setText("About")
        self.connect(about, SIGNAL("triggered()"), self.__showAbout)

        #settings = QAction(self)
        #settings.setText("Settings")

        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        #menubar.addAction(settings)
        menubar.addAction(about)

    def __showAbout(self):
        AboutDialog().exec_()

    def leaderboard_button_pushed(self):
        users = foursquare.users_leaderboard(foursquare.CacheOrNull)
        w = UserListWindow("Leaderboard", users, self)
        t = UserUpdaterThread(w, foursquare.users_leaderboard, self)
        t.start()
        if users:
            w.show()
        else:
            self.showWaitingDialog.emit()

    def logout_pushed(self):
        config_del("code")
        config_del("access_token")
        msgBox = QMessageBox()
        msgBox.setText("I've gotten rid of your credentials. I'm going to close now, and if you run me again, it'll be like our first time all over again. Bye!")
        msgBox.setWindowTitle("Credentials forgotten")
        msgBox.exec_()
        self.close()

    def previous_venues_pushed(self):
        venues = foursquare.get_history(foursquare.CacheOrNull)
        w = VenueListWindow("Visited Venues", venues, self)
        t = VenueProviderThread(w, foursquare.get_history, self)
        t.start()
        if venues:
            w.show()
        else:
            self.showWaitingDialog.emit()

    def todo_venues_pushed(self):
        try:
            venues = foursquare.lists_todos(foursquare.CacheOrNull)
            w = VenueListWindow("To-Do Venues", venues, self)
            t = VenueProviderThread(w, foursquare.lists_todos, self)
            t.start()
            if venues:
                w.show()
            else:
                self.showWaitingDialog.emit()
        except IOError:
            self.networkError.emit()

    def search_venues_pushed(self):
        dialog = SearchDialog(self)
        dialog.exec_()

        if (dialog.result() != QDialog.Accepted):
            return None

        venueName = dialog.text().encode('utf-8')
        categoryId = dialog.category()
        ll = LocationProvider().get_ll()

        try:
            venues = foursquare.venues_search(venueName, ll, categoryId, foursquare.DEFAULT_FETCH_AMOUNT, foursquare.CacheOrNull)
            v = VenueListWindow("Search results", venues, self)
            t = VenueSearchThread(v, foursquare.venues_search, venueName, ll, categoryId, foursquare.DEFAULT_FETCH_AMOUNT, self)
            t.start()
            if venues:
                v.show()
            else:
                self.showWaitingDialog.emit()
        except IOError:
            self.networkError.emit()

    def locationSelected(self, index):
        LocationProvider().select(index)
        foursquare.config_set("locationProvider", index)

    def new_venue_pushed(self):
        try:
            w = NewVenueWindow(self, foursquare.get_venues_categories(), LocationProvider().get_ll())
            w.show()
        except IOError:
            self.networkError.emit()

    def setVenues(self, venues):
        self.__venues = venues

    def venues(self):
        return self.__venues

    def setUsers(self, venues):
        self.__users = venues

    def users(self):
        return self.__users

    def settings_button_pushed(self):
        SettingsDialog(self).show()


class SettingsDialog(UberSquareWindow):
    def __init__(self, parent = None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        
        self.cw = QWidget(self)
        self.setCentralWidget(self.cw)

        layout = QGridLayout(self.cw)
        layout.setContentsMargins(22, 22, 22, 22)

        notice = "Yo'll need to link your facebook/twitter account from the foursquare website for these setting to have any effect."
        notice += "  The foursquare API does not offer any means for applications to do this."
        label = QLabel(notice)
        label.setWordWrap(True)

        self.tw = QCheckBox("Post to Twitter")
        self.fb = QCheckBox("Post to Facebook")

        broadcast = foursquare.config_get("broadcast")
        if broadcast:
            if not ", " in broadcast:
                self.tw.setChecked("twitter" in broadcast)
                self.fb.setChecked("facebook" in broadcast)

        self.saveButton = QPushButton("Save")
        self.connect(self.saveButton, SIGNAL("clicked()"), self.save)

        layout.addWidget(label, 0, 0)
        layout.addWidget(self.tw, 1, 0)
        layout.addWidget(self.fb, 2, 0)
        layout.addWidget(self.saveButton, 3, 0)
        layout.setRowStretch(4, 3)

    def save(self):
        broadcast = "public"
        if self.tw.isChecked():
            broadcast += ",twitter"
        if self.fb.isChecked():
            broadcast += ",facebook"

        foursquare.config_set("broadcast", broadcast)
        self.close()


class SearchDialog(QDialog):
    def __init__(self, parent):
        super(SearchDialog, self).__init__(parent)
        self.setWindowTitle("Search")
        self.centralWidget = QWidget()

        #Main Layout
        layout = QGridLayout()
        #layout.setSpacing(0)
        self.setLayout(layout)

        self.searchQuery = QLineEdit(self)
        self.searchQuery.setPlaceholderText("Search query")

        button = QPushButton("Search")
        self.connect(button, SIGNAL("clicked()"), self.accept)

        self.categorySelector = CategorySelector()

        layout.addWidget(self.categorySelector, 0, 0, 1, 2)
        layout.addWidget(self.searchQuery, 1, 0)
        layout.addWidget(button, 1, 1)

    def category(self):
        return self.categorySelector.selectedCategory()

    def text(self):
        return self.searchQuery.text()


def start():
    app = QApplication(sys.argv)

    token_present = foursquare.config_get("access_token") != None

    if not token_present:
        msgBox = QMessageBox()
        msgBox.setText("Hi! It looks like this is the first run!\n\nI'm going to open a browser window now, and I need you to authorize me so I can get data/do your check-ins, etc.")
        msgBox.setWindowTitle("First run")
        msgBox.addButton("Ok", QMessageBox.AcceptRole)
        msgBox.addButton("Cancel", QMessageBox.RejectRole)
        msgBox.exec_()
        if msgBox.buttonRole(msgBox.clickedButton()) == QMessageBox.AcceptRole:
            foursquare_auth.fetch_code()
            foursquare_auth.fetch_token()
            token_present = True
            d = QMessageBox()
            d.setWindowTitle("Image cache")
            d.setText("In order to save bandwidth, category images are cached.  To download these images for a first time, click \"Update image cache\". This'll take some time, but will <b>really</b> speed up searches.")
            d.addButton("Ok", QMessageBox.YesRole)
            d.exec_()

    if token_present:
        try:
            foursquare.get_user("self", foursquare.CacheOrGet)
        except IOError:
            d = QMessageBox()
            d.setWindowTitle("Network Error")
            d.setText("I couldn't connect to foursquare to retrieve data. Make sure yo're connected to the internet, and try again (keep in mind that it may have been just a network glitch).")
            d.addButton("Ok", QMessageBox.YesRole)
            d.exec_()

        main_window = MainWindow()
        main_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    start()
