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
from xdg import BaseDirectory

CLIENT_ID="A0IJ0P4EFRO50JUEYALJDGR52RDS0O4H1OKPSIEYZ5LHSNGH"
CLIENT_SECRET="ACDUWAODBXRUPXHMVVWOXXATFN0PM0GP2PSLI5MZZCTUQ2TV"
CALLBACK_URI="http://localhost:6060/auth"

authData = dict()

BASE_URL="https://api.foursquare.com/v2/"
API_VERSION = "20120208"
DEBUG = False

cache_dir = os.path.join(BaseDirectory.xdg_cache_home, "ubersquare/")
image_dir = os.path.join(BaseDirectory.xdg_data_home, "ubersquare/images/")
config_dir = os.path.join(BaseDirectory.xdg_config_home, "ubersquare/")

if not os.path.exists(cache_dir):
	os.makedirs(cache_dir)
if not os.path.exists(image_dir):
	os.makedirs(image_dir)
if not os.path.exists(config_dir):
	os.makedirs(config_dir)

query_cache = cache_dir + "cache.sqlite"
if not os.path.exists(query_cache):
	conn = sqlite3.connect(query_cache)
	conn.execute("CREATE TABLE IF NOT EXISTS queries (resource TEXT PRIMARY KEY, value TEXT)")
	#conn.execute("CREATE TABLE IF NOT EXISTS tips (tipId TEXT PRIMARY KEY, venueID TEXT, done BOOLEAN, todo BOOLEAN, tipText TEXT)")
	conn.close()

config = config_dir + "config.sqlite"
if not os.path.exists(config):
	conn = sqlite3.connect(config)
	conn.execute("CREATE TABLE IF NOT EXISTS config (property TEXT PRIMARY KEY, value TEXT)")
	conn.close()

def debug(string):
	print string

def debug_json(string):
	print json.dumps(string, sort_keys=True, indent=4)

####################
# CACHE/FOURSQUARE #
####################

def config_set(property, value):
	conn = sqlite3.connect(config)
	conn.execute("INSERT OR REPLACE INTO config VALUES (?, ?)", (property, value))
	conn.commit()
	conn.close()

def config_del(property):
	conn = sqlite3.connect(config)
	conn.execute("DELETE FROM config WHERE property = ?", (property,))
	conn.commit()
	conn.close()

def config_get(property):
	value = None
	conn = sqlite3.connect(config)
	c = conn.cursor()
	c.execute("SELECT value FROM config WHERE property = ?", (property,))
	row = c.fetchone()
	if not row is None:
		value = row[0]
	conn.commit()
	conn.close()
	return value


# True and False are to mantain some legacy code, but *will* be deprecated.
CacheOnly = 3
CacheIfPosible = True
NoCache = False

CacheOrNull = 3
CacheOrGet = True
ForceFetch = False

class Cache:
	CacheOrNull = 3
	CacheOrGet = True
	ForceFetch = False	

def cacheModeToString(cacheMode):
	if cacheMode == CacheOnly:
		return "Get from cache or return null"
	elif cacheMode == CacheIfPosible:
		return "Get from cache or foursquare"
	elif cacheMode == NoCache:
		return "Don't read from cache"

def foursquare_get(path, params, read_cache = False, callback = None):
	commonParams = {'oauth_token': authData['ACCESS_TOKEN'], 'v': API_VERSION}
	allParams = urllib.urlencode(dict(commonParams.items() + params.items()))

	resource = path + "?" + allParams
	conn = sqlite3.connect(query_cache)

	print "-----"
	print "Getting " + resource
	print "Using cache: " + cacheModeToString(read_cache) + "..."
	
	c = conn.cursor()
	if read_cache == CacheOrGet or read_cache == CacheOrNull:
		c.execute("SELECT value FROM queries WHERE resource = ?", (resource,))
		row = c.fetchone()
		conn.close()
		if row is None:
			if read_cache == CacheOrGet:
				return foursquare_get(path, params, NoCache, callback)
			else:
				return None
		else:
			response = row[0]
	else:
		response = urllib.urlopen(BASE_URL + resource).read()
		c.execute("INSERT OR REPLACE INTO queries VALUES (?, ?)", (resource, response))
		conn.commit()

	conn.close()

	if response:
		response = json.loads(response,"UTF-8")
	return response

def foursquare_post(path, params):
	commonParams = {'oauth_token': authData['ACCESS_TOKEN'], 'v': API_VERSION}
	allParams = dict(commonParams.items() + params.items())

	allParams = dict([k, v.encode('utf-8')] for k, v in allParams.items())

	allParams = urllib.urlencode(allParams)

	resource = urllib.urlopen(BASE_URL + path, allParams)
	response = json.load(resource, "UTF-8")
	debug_json(response)
	return response

def image(path):
	url = urlparse(path)
	localdir = image_dir + os.path.dirname(url.path)
	localfile = image_dir + url.path

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
	response = foursquare_get("users/self/venuehistory", {}, read_cache)
	if response:
		return build_venue_array(response[u'response'][u'venues'][u'items'])

def lists_todos(read_cache):
	response = foursquare_get("lists/self/todos", {}, read_cache)
	if response:
		return build_venue_array(response[u'response'][u'list'][u'listItems'][u'items'])

def venues_search(query, ll, category = "", intent = "checkin", limit = 25):
	response = foursquare_get("venues/search", {'query': query, 'll': ll, 'intent' : intent, 'categoryId' : category, 'limit': limit})
	if response:
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
	response = foursquare_get("users/" + uid, {}, read_cache)
	if response:
		return response[u'response']

def get_venue(venueId):
	response = foursquare_get("/venues/%s?" % venueId, {})
	if response:
		return response[u'response'][u'venue']

def checkin(venue, ll, shout = ""):
	"""
	Checks in the user at venue with lat/lng ll
	"""
	response = foursquare_post("/checkins/add", {'shout': shout, 'venueId': venue[u'id'], 'broadcast': "public,facebook", 'll': ll})
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

def get_venues_categories(readCache = Cache.CacheOrGet):
	"""
	Returns a hierarchical list of categories applied to venues.
	"""
	response = foursquare_get("venues/categories", {}, readCache)
	if response:
		return response[u'response'][u'categories']

def venue_add(venue, ignoreDuplicates = False, ignoreDuplicatesKey = None):
	"""
	required: name, ll
	optional: address, crossAddress, city, state, zip, phone, twitter, primaryCategoryId, description, url
	second_run: ignoreDuplicates, ignoreDuplicatesKey
	"""
	response = foursquare_post("venues/add", venue)
	return response

def venues_venue(venueId, readCache = CacheIfPosible):
	response = foursquare_get("venues/" + venueId, {}, readCache)
	if response:
		#response > venue > tips > groups [] > items [] >
		return response[u'response'][u'venue']

def users_leaderboard(read_cache):
	response = foursquare_get("users/leaderboard", {}, read_cache)
	if response:
		return response[u'response'][u'leaderboard'][u'items']

def __delete_venue_with_tip(tipId):
	"""
	A nasty hack.  If a tip changes status in a venue, I uncache the venue, since
	the cached data is out-of-date, and manually synching this is pretty hard work
	This may change if future </lie>
	"""
	conn = sqlite3.connect(query_cache)
	conn.execute("DELETE FROM queries WHERE value LIKE ?", ("%"+tipId+"%",))
	conn.commit()
	conn.close()

def tip_add(venueId, text, url = "", broadcast = ""):
	response = foursquare_post("/tips/add", {'venueId': venueId, 'text': text, 'url': url, 'broadcast': broadcast})
	return response

def tip_marktodo(tipId, marked):
	if marked:
		response = foursquare_post("tips/" + tipId + "/marktodo", {})
	else:
		response = foursquare_post("lists/self/todos/deleteitem", { 'itemId': tipId })
	__delete_venue_with_tip(tipId)
	return response

def tip_markdone(tipId, marked):
	if marked:
		response = foursquare_post("tips/" + tipId + "/markdone", {})
	else:
		response = foursquare_post("lists/self/dones/deleteitem", { 'itemId': tipId })
	__delete_venue_with_tip(tipId)
	return response

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
	categories = get_venues_categories(Cache.ForceFetch)
	for category in categories:
		fetch_category_image(category)
	print "done updating image cache"

def init():
	print "Reading code/acces_token"
	authData['CODE'] = config_get("code")
	authData['ACCESS_TOKEN'] = config_get("access_token")

if __name__ == "__main__":
	print "This is the foursquare API library, you're not supposed to run this!"
	sys.exit()
else:
	init()