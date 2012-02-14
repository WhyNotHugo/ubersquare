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
	i = 0;
	for venue in response[u'response'][u'venues'][u'items']:
		venues[i] = venue
		i += 1
	return venues

def get_todo_venues():
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208"})
	response = foursquare_get("lists/self/todos", params)
	venues = dict()
	i = 0;
	for venue in response[u'response'][u'list'][u'listItems'][u'items']:
		venues[i] = venue
		i += 1

	return venues

def venues_search(query, ll, limit = 25):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'query': query, 'll': ll, 'limit': limit})
	response = foursquare_get("venues/search", params)
	venues = dict()
	i = 0;
	for venue in response[u'response'][u'venues']:
		# Esto puede parecer cualquiera, pero es para que tenga el mismo formato que los dem&aacute;s, y sean todas las listas iguales
		venues[i] = dict()
		venues[i][u'venue'] = venue
		i += 1

	return venues

def get_self():
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208"})
	response = foursquare_get("users/self", params)
	return response

def get_venue(venueId):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'group': "created"})
	response = foursquare_get("/venues/%s?" % venueId, params)
	venue = response[u'response'][u'venue']
	return venue

def get_aproximate_location(venue):
	venueId = venue[u'id']
	lat = float((ord(venueId[0]) + (ord(venueId[1])*100)))/(10000*10000) + venue[u'location'][u'lat']
	lat = "%2.8f" % lat
	lng = float((ord(venueId[2]) + (ord(venueId[3])*100)))/(10000*10000) + venue[u'location'][u'lng']
	lng = "%2.8f" % lng
	ll = lat + "," + lng
	return ll

def get_aproximate_location_by_id(venueId):
	venue = get_venue(venueId)
	lat = float((ord(venueId[0]) + (ord(venueId[1])*100)))/(10000*10000) + venue[u'location'][u'lat']
	lat = "%2.8f" % lat
	lng = float((ord(venueId[2]) + (ord(venueId[3])*100)))/(10000*10000) + venue[u'location'][u'lng']
	lng = "%2.8f" % lng
	ll = lat + "," + lng
	return ll

def checkin(venue, ll):
	"""
	Checks in the user at venueId with lat/lng ll
	"""
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'venueId': venue[u'id'], 'broadcast': "public,facebook", 'll': ll})
	response = foursquare_post("/checkins/add", params)
	return response

def checkin_by_id(venueId, ll):
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

if __name__ == "__main__":
	print "This is the foursquare API library, you're not supposed to run this!"
	sys.exit()