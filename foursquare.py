#!/usr/bin/python2
try:
	import json
except ImportError:
	import simplejson as json
import urllib
import sys
import sqlite3
import os
from urlparse import urlparse
import atexit

CLIENT_ID="A0IJ0P4EFRO50JUEYALJDGR52RDS0O4H1OKPSIEYZ5LHSNGH"
CLIENT_SECRET="ACDUWAODBXRUPXHMVVWOXXATFN0PM0GP2PSLI5MZZCTUQ2TV"
CALLBACK_URL="http://localhost:6060/auth"

CODE="MFY3CM12JZHHSR43BJHTNN3C2ZIP3ZQRZNGA1CA35BH1NQMT"
ACCESS_TOKEN="GSMXQNPBOYRT3XM54FKK31EBABYWADDTKEUKNG42JNWQIZZX"

BASE_URL="https://api.foursquare.com/v2/"

DEBUG = False

API_VERSION = "20120208"

cache_dir = "/home/user/.cache/ubersquare/"
image_cache_dir = cache_dir + "images/"
query_cache = cache_dir + "cache.sqlite"

if not os.path.exists(cache_dir):
	os.makedirs(cache_dir)

if not os.path.exists(query_cache):
	conn = sqlite3.connect(query_cache)
	conn.execute("CREATE TABLE queries (resource TEXT PRIMARY KEY, value TEXT)")
	conn.close()

def debug(string):
	if (DEBUG):
		print string

def debug_json(string):
	debug(json.dumps(string, sort_keys=True, indent=4))

####################
# CACHE/FOURSQUARE #
####################

def foursquare_get(path, params, read_cache = False, callback = None):
	resource = path + "?" + params
	conn = sqlite3.connect(query_cache)

	print "-----"
	print "Getting " + resource
	print "Using cache: " + str(read_cache)
	
	c = conn.cursor()
	if read_cache:
		c.execute("SELECT value FROM queries WHERE resource = ?", (resource,))
		row = c.fetchone()
		if row is None:
			url = urllib.urlopen(BASE_URL + resource)
			response = url.read()
			c.execute("INSERT INTO queries VALUES (?, ?)", (resource, response))
			conn.commit()
		else:
			response = row[0]
	else:
		url = urllib.urlopen(BASE_URL + resource)
		response = url.read()
		c.execute("UPDATE queries SET value = ?  WHERE resource = ?", (response, resource))
		conn.commit()

	conn.close()

	print "Done!"

	response = json.loads(response,"UTF-8")
	debug_json(response)
	return response

def foursquare_post(path, params):
	resource = urllib.urlopen(BASE_URL + path, params)
	response = json.load(resource, "UTF-8")
	debug_json(response)
	return response

def image(path):
	url = urlparse(path)
	localdir = image_cache_dir + os.path.dirname(url.path)
	localfile = image_cache_dir + url.path

	if not os.path.exists(localdir):
		os.makedirs(localdir)

	if not os.path.exists(localfile):
		print "Fetching image " + path + "..."
		u = urllib.urlopen(path)
		f = open(localfile, "w")
		f.write(u.read())
		f.close()

	return localfile

#######################
# AUXILIARY FUNCTIONS #
#######################

def build_venue_array(source):
	venues = dict()
	i = 0;
	for venue in source:
		if u'beenHere' in venue:
			 # Dirty, but the the model is too much in use to avoid this at 4am
			venue[u'venue'][u'beenHere'] = venue[u'beenHere']
		venues[i] = venue
		i += 1
	return venues

###############################################################################

def get_history(read_cache):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': API_VERSION, 'group': "created"})
	response = foursquare_get("users/self/venuehistory", params, read_cache)
	return build_venue_array(response[u'response'][u'venues'][u'items'])

def get_todo_venues(read_cache):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': API_VERSION})
	response = foursquare_get("lists/self/todos", params, read_cache)
	return build_venue_array(response[u'response'][u'list'][u'listItems'][u'items'])

def venues_search(query, ll, limit = 25):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': API_VERSION, 'query': query, 'll': ll, 'limit': limit})
	response = foursquare_get("venues/search", params)
	venues = dict()
	i = 0;
	for venue in response[u'response'][u'venues']:
		# Esto puede parecer cualquiera, pero es para que tenga el mismo formato que los dem&aacute;s, y sean todas las listas iguales
		venues[i] = dict()
		venues[i][u'venue'] = venue
		i += 1

	return venues

def get_user(uid, read_cache):
	"""
	Returns profile information for a given user, including selected badges and mayorships.
	"""
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': API_VERSION})
	response = foursquare_get("users/" + uid, params, read_cache)
	return response[u'response']

def get_venue(venueId):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': API_VERSION, 'group': "created"})
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

def checkin(venue, ll, shout = ""):
	"""
	Checks in the user at venue with lat/lng ll
	"""
	params = urllib.urlencode({'shout': shout, 'oauth_token': ACCESS_TOKEN, 'v': API_VERSION, 'venueId': venue[u'id'], 'broadcast': "public,facebook", 'll': ll})
	response = foursquare_post("/checkins/add", params)
	return response

def get_last_ll():
	"""
	Returns the ll of the user's last checkin
	"""
	ll = dict()
	for item in get_user("self", False)[u'user'][u'checkins'][u'items']:
		if item[u'type'] == "checkin":
			ll['lat'] = item[u'venue'][u'location'][u'lat']
			ll['lng'] = item[u'venue'][u'location'][u'lng']
	if 'lat' in ll:
		ll = "%(lat)2.6f,%(lng)2.6f" % ll
	else:
		ll = "-34.596059,-58.398606"
		print "WARNING: no LL provided!"

	return ll

def get_venues_categories():
	"""
	Returns a hierarchical list of categories applied to venues.
	"""
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': API_VERSION})
	response = foursquare_get("venues/categories", params, True)
	return response[u'response'][u'categories']

def venue_add(venue, ignoreDuplicates = False, ignoreDuplicatesKey = None):
	"""
	required: name, ll
	optional: address, crossAddress, city, state, zip, phone, twitter, primaryCategoryId, description, url
	second_run: ignoreDuplicates, ignoreDuplicatesKey
	"""
	params = {'oauth_token': ACCESS_TOKEN, 'v': API_VERSION}
	params = dict(params.items() + venue.items())
	params = urllib.urlencode(params)

	response = foursquare_post("venues/add", params)

	return response

def users_leaderboard(read_cache):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': API_VERSION})
	response = foursquare_get("users/leaderboard", params, read_cache)
	return response[u'response'][u'leaderboard'][u'items']

############################
# Extra one-time functions #
############################

def fetch_category_image(category):
	prefix = category[u'icon'][u'prefix']
	extension = category[u'icon'][u'name']
	image(prefix + "64" + extension)
	if u'categories' in category:
		for category in category[u'categories']:
			fetch_category_image(category)

def init_category_icon_cache():
	categories = get_venues_categories()
	for category in categories:
		fetch_category_image(category)
	

if __name__ == "__main__":
	print "This is the foursquare API library, you're not supposed to run this!"
	sys.exit()