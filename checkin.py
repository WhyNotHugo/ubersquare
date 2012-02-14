#!/usr/bin/python2

import sys
from foursquare import *
try:
	import location
except ImportError:
	print "Couldn't import location. You're probably not running maemo."
	print "GPS Support disabled."

def interactive_checkin_id(venueId):
	venue = get_venue(venueId)
	proceed = raw_input("Check in at " + repr(venue[u'name']) + ", " + repr(venue[u'location'][u'address']) + "?")
	if (proceed == "y"):
		ll = get_aproximate_location_by_id(venueId)
		response = checkin(venueId,ll)
		print "Checked into " + venueId + " using " + ll
		for item in response[u'notifications']:
			# if u'message' in item:
			# 	print item[u'message']
			if item[u'type'] == "message":
				print "%s" % item[u'item'][u'message']
			elif item[u'type'] == "score":
				print "Total points: %d" % item[u'item'][u'total']
				for score in item[u'item'][u'scores']:
					print "%(points)d\t%(message)s" % \
					{'points': score[u'points'], 'message' : score[u'message']}
			
	else:
		print "Aborted"

def interactive_chekin(venues):
	"""
	Recives a dict (num => venue) and wait for a user to input one of these numbers.
	Will checkin at that location with auto-generated lat/lng
	"""
	i = int(raw_input("Select venue: "))
	interactive_checkin_id(venues[i][u'venue'][u'id'])

def interactive_history():
	"""
	Shows a list of recent places, a number to associate them,
	and return this as a dict (num => venue).
	"""

	i = 0
	for venue in get_history():
		print "%(num)d\t%(name)s" % {'num' : i, 'name': venue[u'name']}
		i += 1
	return venues

def interactive_ll():
	print get_last_ll()

def print_gps(device, user_data):
	if not device:
		return
	if device.fix:
		if device.fix[1] & location.GPS_DEVICE_LATLONG_SET:
			print "lat = %f, long = %f" % device.fix[4:6]
		if device.fix[1] & location.GPS_DEVICE_ALTITUDE_SET:
			print "alt = %f" % device.fix[7]
		print "horizontal accuracy: %f meters" % (device.fix[6] / 100)
 
def get_gps_ll():
	control = location.GPSDControl.get_default()
	device = location.GPSDevice()

	control.set_properties(preferred_method=location.METHOD_ACWP|location.METHOD_AGNSS)
	control.start()

	print device.fix
	print device.status
	import time
	while True:
		print device.fix
		print device.status
		time.sleep(5)


if __name__ == "__main__":
	if (len(sys.argv) == 3):
		if (sys.argv[1] == "ci"):
			interactive_checkin_id(sys.argv[2])
		if (sys.argv[1] == "ex"):
			interactive_checkin_id(sys.argv[2])
	elif (len(sys.argv) == 2):
		if (sys.argv[1] == "ci"):
			interactive_chekin(interactive_history())
		if (sys.argv[1] == "ll"):
			interactive_ll()
		if (sys.argv[1] == "log"):
			interactive_history()
		if (sys.argv[1] == "gps"):
			get_gps_ll()
	else:
		print "USAGE: ... COMMAND ID"
		sys.exit()