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

from PySide.QtCore import QThread
import foursquare
import time


class VenueProviderThread(QThread):
	def __init__(self, venueWindow, source, parent):
		super(VenueProviderThread, self).__init__(parent)
		self.venueWindow = venueWindow
		self.source = source
		self.parentWindow = parent

	def run(self):
		try:
			venues = self.source(foursquare.ForceFetch)
			self.parentWindow.setVenues(venues)
			self.parentWindow.hideWaitingDialog.emit()
			self.venueWindow.updateVenues.emit()
		except IOError:
			self.parentWindow.networkError.emit()


class VenueSearchThread(VenueProviderThread):
	def __init__(self, venueWindow, source, venueName, ll, categoryId, limit, parent):
		super(VenueSearchThread, self).__init__(venueWindow, source, parent)
		self.venueWindow = venueWindow
		self.venueName = venueName
		self.ll = ll
		self.categoryId = categoryId
		self.limit = limit

	def run(self):
		try:
			venues = self.source(self.venueName, self.ll, self.categoryId, self.limit, foursquare.ForceFetch)
			self.parentWindow.setVenues(venues)
			self.parentWindow.hideWaitingDialog.emit()
			self.venueWindow.updateVenues.emit()
		except IOError:
			self.parentWindow.networkError.emit()


class UserUpdaterThread(QThread):
	def __init__(self, target, source, parent):
		super(UserUpdaterThread, self).__init__(parent)
		self.target = target
		self.source = source
		self.parentWindow = parent

	def run(self):
		try:
			users = self.source(foursquare.ForceFetch)
			self.parentWindow.setUsers(users)
			self.parentWindow.hideWaitingDialog.emit()
			self.target.updateUsers.emit()
		except IOError:
			self.parentWindow.networkError.emit()
		return 0


class ImageCacheThread(QThread):
	def __init__(self, parent):
		super(ImageCacheThread, self).__init__(parent)
		self.__parent = parent

	def run(self):
		try:
			foursquare.init_category_icon_cache()
			self.__parent.hideWaitingDialog.emit()
		except IOError:
			self.__parent.hideWaitingDialog.emit()
			self.__parent.networkError.emit()


class TipMarkDoneBackgroundThread(QThread):
	def __init__(self, tipId, marked, parent):
		super(TipMarkDoneBackgroundThread, self).__init__(parent)
		self.parentWindow = parent
		self.marked = marked
		self.tipId = tipId

	def run(self):
		try:
			foursquare.tip_markdone(self.tipId, self.marked)
		except IOError:
			self.parentWindow.networkError.emit()


class TipMarkTodoBackgroundThread(QThread):
	def __init__(self, tipId, marked, parent):
		super(TipMarkTodoBackgroundThread, self).__init__(parent)
		self.parentWindow = parent
		self.marked = marked
		self.tipId = tipId

	def run(self):
		try:
			foursquare.tip_marktodo(self.tipId, self.marked)
		except IOError:
			self.parentWindow.networkError.emit()


class UpdateSelf(QThread):
	def __init__(self, parent):
		super(UpdateSelf, self).__init__(parent)
		self.__parent = parent

	def run(self):
		try:
			foursquare.get_user("self", foursquare.ForceFetch)
			self.__parent.selfUpdated.emit()
		except IOError:
			self.__parent.networkError.emit()


class LeaveTipThread(QThread):
	def __init__(self, venueId, text, parent):
		super(LeaveTipThread, self).__init__(parent)
		self.venueId = venueId
		self.text = text
		self.parentWindow = parent

	def run(self):
		try:
			foursquare.tip_add(self.venueId, self.text)
			self.parentWindow.hideWaitingDialog.emit()
			self.parentWindow.showMoreInfo.emit()
		except IOError:
			self.parentWindow.networkError.emit()


class VenueDetailsThread(QThread):
	def __init__(self, venueId, parent):
		super(VenueDetailsThread, self).__init__(parent)
		self.__parent = parent
		self.venueId = venueId

	def run(self):
		try:
			venue = foursquare.venues_venue(self.venueId, foursquare.ForceFetch)
			if u'mayor' in venue:
				if u'user' in venue[u'mayor']:
					print "there's a mayor!"
					foursquare.image(venue[u'mayor'][u'user'][u'photo'])
			self.__parent.hideWaitingDialog.emit()
			# This tiny sleep in necesary to (a) Avoid an Xorg warning, (b) achieve a smoother transition
			time.sleep(0.15)
			self.__parent.showMoreInfo.emit()
		except IOError:
			self.__parent.hideWaitingDialog.emit()
			self.__parent.networkError.emit()
		self.exec_()
		self.exit(0)

class UserDetailsThread(QThread):
	def __init__(self, userId, parent):
		super(UserDetailsThread, self).__init__(parent)
		self.__parent = parent
		self.userId = userId

	def run(self):
		try:
			user = foursquare.get_user(self.userId, foursquare.ForceFetch)
			photo = user[u'user'][u'photo']
			foursquare.image(photo)
			self.__parent.hideWaitingDialog.emit()
			self.__parent.showUser.emit()
		except IOError:
			self.__parent.hideWaitingDialog.emit()
			self.__parent.networkError.emit()
		self.exec_()
		self.exit(0)