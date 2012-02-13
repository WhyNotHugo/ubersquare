#!/usr/bin/python2
try:
	import json
except ImportError:
	import simplejson as json
import urllib
import sys

CLIENT_ID="A0IJ0P4EFRO50JUEYALJDGR52RDS0O4H1OKPSIEYZ5LHSNGH"
CLIENT_SECRET="ACDUWAODBXRUPXHMVVWOXXATFN0PM0GP2PSLI5MZZCTUQ2TV"
CALLBACK_URL="http://localhost:6060/auth"

CODE="MFY3CM12JZHHSR43BJHTNN3C2ZIP3ZQRZNGA1CA35BH1NQMT"
ACCESS_TOKEN="GSMXQNPBOYRT3XM54FKK31EBABYWADDTKEUKNG42JNWQIZZX"

BASE_URL="https://api.foursquare.com/v2/"

DEBUG = False

def debug(string):
	if (DEBUG):
		print string

def debug_json(string):
	debug(json.dumps(string, sort_keys=True, indent=4))

def foursquare_get(path, params):
	f = urllib.urlopen(BASE_URL + path + "?" + params)
	response = json.load(f,"UTF-8")
	debug_json(response)
	return response

def foursquare_post(path, params):
	f = urllib.urlopen(BASE_URL + path, params)
	response = json.load(f,"UTF-8")
	debug_json(response)
	return response

def get_history():
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'group': "created"})
	response = foursquare_get("users/self/venuehistory", params)
	venues = dict()
	for item in response[u'response'][u'venues'][u'items']:
		venues[item[u'venue'][u'id']]=item[u'venue']

	#return venues
	return response

def get_self():
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208"})
	response = foursquare_get("users/self", params)
	return response

def get_venue(venueId):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'group': "created"})
	response = foursquare_get("/venues/%s?" % venueId, params)
	venue = response[u'response'][u'venue']
	return venue

def get_aproximate_location(venueId):
	venue = get_venue(venueId)
	lat = float((ord(venueId[0]) + (ord(venueId[1])*100)))/(10000*10000) + venue[u'location'][u'lat']
	lat = "%2.8f" % lat
	lng = float((ord(venueId[2]) + (ord(venueId[3])*100)))/(10000*10000) + venue[u'location'][u'lng']
	lng = "%2.8f" % lng
	ll = lat + "," + lng
	return ll

def checkin(venueId, ll):
	"""
	Checks in the user at venueId with lat/lng ll
	"""
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'venueId': venueId, 'broadcast': "public,facebook", 'll': ll})
	response = foursquare_post("/checkins/add", params)
	return response

def get_last_ll():
	ll = dict()
	for item in get_self()[u'response'][u'user'][u'checkins'][u'items']:
		if item[u'type'] == "checkin":
			ll['lat'] = item[u'venue'][u'location'][u'lat']
			ll['lng'] = item[u'venue'][u'location'][u'lng']
	ll = "%(lat)2.6f,%(lng)2.6f" % ll
	return ll
	
#####################################

def interactive_checkin_id(venueId):
	venue = get_venue(venueId)
	proceed = raw_input("Check in at " + repr(venue[u'name']) + ", " + repr(venue[u'location'][u'address']) + "?")
	if (proceed == "y"):
		ll = get_aproximate_location(venueId)
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
	venues = dict()
	i = 1;
	for venue in get_history()[u'response'][u'venues'][u'items']:
		venues[i] = venue
		print "%(num)d\t%(name)s" % {'num' : i, 'name': venue[u'venue'][u'name']}
		i += 1
	return venues

def interactive_ll():
	print get_last_ll()

# def explore_near_last():
# 	p

#def search

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
	else:
		print "USAGE: ... COMMAND ID"
		sys.exit()