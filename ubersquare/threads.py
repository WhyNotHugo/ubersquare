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
from foursquare import Cache

class VenueProviderThread(QThread):
	def __init__(self, target, source, parent):
		super(VenueProviderThread, self).__init__(parent)
		self.target = target
		self.source = source
		self.parentWindow = parent
	
	def run(self):
		try:
			venues = self.source(Cache.ForceFetch)
			self.parentWindow.setVenues(venues)
			self.parentWindow.hideWaitingDialog.emit()
			self.target.updateVenues.emit()
		except IOError:
			self.parentWindow.networkError.emit()
		self.exec_()
		self.exit(0)

class UserUpdaterThread(QThread):
	def __init__(self, target, source, parent):
		super(UserUpdaterThread, self).__init__(parent)
		self.target = target
		self.source = source
		self.parentWindow = parent
	
	def run(self):
		try:
			users = self.source(Cache.ForceFetch)
			self.parentWindow.setUsers(users)
			self.parentWindow.hideWaitingDialog.emit()
			self.target.updateUsers.emit()
		except IOError:
			self.parentWindow.networkError.emit()
		self.exec_()
		self.exit(0)

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
		self.exec_()
		self.exit(0)

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
		self.exec_()
		self.exit(0)

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
		self.exec_()
		self.exit(0)

class UpdateSelf(QThread):
	def __init__(self, parent):
		super(UpdateSelf, self).__init__(parent)
		self.__parent = parent

	def run(self):
		try:
			foursquare.get_user("self", Cache.ForceFetch)
			self.__parent.selfUpdated.emit()
		except IOError:
			self.__parent.networkError.emit()
		self.exec_()
		self.exit(0)