try:
	import location
except ImportError:
	print "Couldn't import location. You're probably not running maemo."
	print "GPS Support disabled."

import foursquare

class FullAGPSLocationProvider:
	def __init__(self):
		try:
			self.control = location.GPSDControl.get_default()
			self.device = location.GPSDevice()

			self.control.set_properties(preferred_method=location.METHOD_ACWP|location.METHOD_AGNSS)
		except NameError:
			return

	def get_ll(self):
		lat = "%2.8f" % self.device.fix[4]
		lng = "%2.8f" % self.device.fix[5]
		return lat + "," + lng

class LastCheckinLocationProvider:
	def get_ll(self):
		return foursquare.get_last_ll()

class AproximateVenueLocationProvider:
	# This code is a duplicate of foursquare.get_aproximate_location(venue)
	def __init__(self, venue):
		self.venue = venue

	def get_ll(self):
		venueId = self.venue[u'id']
		lat = float((ord(venueId[0]) + (ord(venueId[1])*100)))/(10000*10000) + self.venue[u'location'][u'lat']
		lat = "%2.8f" % lat
		lng = float((ord(venueId[2]) + (ord(venueId[3])*100)))/(10000*10000) + self.venue[u'location'][u'lng']
		lng = "%2.8f" % lng
		ll = lat + "," + lng
		return ll