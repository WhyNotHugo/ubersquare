# -*- coding: utf-8 -*-

# Copyright (c) 2012 Hugo Osvaldo Barrera <hugo@osvaldobarrera.com.ar>
#
# Permission todo use, copy, modify, and distribute this software for any
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
from xdg import BaseDirectory

###################
# LOCAL CONSTANTS #
###################

CLIENT_ID     = "A0IJ0P4EFRO50JUEYALJDGR52RDS0O4H1OKPSIEYZ5LHSNGH"
CLIENT_SECRET = "ACDUWAODBXRUPXHMVVWOXXATFN0PM0GP2PSLI5MZZCTUQ2TV"
CALLBACK_URI  = "http://localhost:6060/auth"

BASE_URL = "https://api.foursquare.com/v2/"
API_VERSION = "20120208"
DEBUG = False

BROADCAST_DEFAULT = "public"

####################
# GLOBAL CONSTANTS #
####################

DEFAULT_FETCH_AMOUNT = 25

#########################
# FILES AND DIRECTORIES #
#########################

# Directory that contains the cache
cache_dir = os.path.join(BaseDirectory.xdg_cache_home, "ubersquare/")
# Directory that contains cached images
image_dir = os.path.join(BaseDirectory.xdg_data_home, "ubersquare/images/")
# Directory that contains the configuration
config_dir = os.path.join(BaseDirectory.xdg_config_home, "ubersquare/")

# Create missing directories
if not os.path.exists(cache_dir):
	os.makedirs(cache_dir)
if not os.path.exists(image_dir):
	os.makedirs(image_dir)
if not os.path.exists(config_dir):
	os.makedirs(config_dir)

def create_cache_db():
	conn = sqlite3.connect(query_cache)
	conn.execute("CREATE TABLE IF NOT EXISTS queries (resource TEXT PRIMARY KEY, value TEXT)")
	conn.close()

def create_config_db():
	conn = sqlite3.connect(config)
	conn.execute("CREATE TABLE IF NOT EXISTS config (property TEXT PRIMARY KEY, value TEXT)")
	conn.close()



query_cache = cache_dir + "cache.sqlite"
if not os.path.exists(query_cache):
	create_cache_db();

config = config_dir + "config.sqlite"
if not os.path.exists(config):
	create_config_db()
	
authData = dict()

#######################
# AUX DEBUG FUNCTIONS #
#######################

def debug(string):
	print string


def debug_json(string):
	print json.dumps(string, sort_keys=True, indent=4)

def cacheModeToString(cacheMode):
	if cacheMode == CacheOnly:
		return "Get from cache or return null"
	elif cacheMode == CacheIfPosible:
		return "Get from cache or foursquare"
	elif cacheMode == NoCache:
		return "Don't read from cache"

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


# All these values are used throughout the system, but the class Cache
# should override them all, and these six fields should dissapear

# Usage of True/False has to be purged everywhere as well, that's really old code!
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


def foursquare_get(path, params, read_cache=False, callback=None):
	"""
	Performs an HTTP get on PATH.
	"""
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
		response = json.loads(response, "UTF-8")
	return response


def foursquare_post(path, params):
	commonParams = {'oauth_token': authData['ACCESS_TOKEN'], 'v': API_VERSION}
	allParams = dict(commonParams.items() + params.items())
	allParams = dict([k, v.encode('utf-8')] for k, v in allParams.items())
	allParams = urllib.urlencode(allParams)

	debug_json(allParams)

	resource = urllib.urlopen(BASE_URL + path, allParams)
	response = json.load(resource, "UTF-8")
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
	i = 0
	for venue in source:
		if 'beenHere' in venue:
			 # Dirty, but the the model is too much in use to avoid this at 4am
			venue['venue']['beenHere'] = venue['beenHere']
		venues[i] = venue
		i += 1
	return venues

###############################################################################
# All these method names need refactoring.  They should be similar to the foursquare API,
# ie: calls to endpoint "user/$UID/tips" should be user_tips(uid)

# Better still, there should be actual objects to do this;
# users.tips(uid)


def get_history(read_cache):
	response = foursquare_get("users/self/venuehistory", {}, read_cache)
	if response:
		return build_venue_array(response['response']['venues']['items'])


def lists_todos(read_cache):
	response = foursquare_get("lists/self/todos", {}, read_cache)
	if response:
		return build_venue_array(response['response']['list']['listItems']['items'])


def venues_search(query, ll, category, limit, read_cache):
	response = foursquare_get("venues/search", {'query': query, 'll': ll, 'intent': "checkin", 'categoryId': category, 'limit': limit}, read_cache)
	if response:
		venues = dict()
		i = 0
		for venue in response['response']['venues']:
			# Esto puede parecer cualquiera, pero es para que tenga el mismo formato que los dem&aacute;s, y sean todas las listas iguales
			venues[i] = dict()
			venues[i]['venue'] = venue
			i += 1
		return venues


def get_user(uid, read_cache):
	"""
	Returns profile information for a given user, including selected badges and mayorships.
	"""
	response = foursquare_get("users/" + uid, {}, read_cache)
	if response:
		return response['response']


def get_venue(venueId):
	response = foursquare_get("/venues/%s?" % venueId, {})
	if response:
		return response['response']['venue']


# TODO: make this entire file OO, and this an actual attribute of it
checkin_hooks = list()
def checkin(venue, ll, shout="", broadcast=None):
	"""
	Checks in the user at venue with lat/lng ll
	"""
	if not broadcast:
		broadcast = config_get("broadcast")
		if broadcast == None:
			broadcast = BROADCAST_DEFAULT

	print "Checking in with broadcast = " + broadcast

	response = foursquare_post("/checkins/add", {'shout': shout, 'venueId': venue['id'], 'broadcast': broadcast, 'll': ll})

	# This is, without doubt, the nastiest hack I've ever done!
	print len(checkin_hooks)
	for hook in checkin_hooks:
		hook()
	
	return response


def add_checkin_hook(hook):
	checkin_hooks.append(hook)


def get_last_ll():
	"""
	Returns the ll of the user's last checkin
	"""
	ll = dict()
	for item in get_user("self", False)['user']['checkins']['items']:
		if item['type'] == "checkin":
			ll['lat'] = item['venue']['location']['lat']
			ll['lng'] = item['venue']['location']['lng']
	if 'lat' in ll:
		ll = "%(lat)2.6f,%(lng)2.6f" % ll
	else:
		ll = "-34.596059,-58.398606"
		print "WARNING: no LL provided!"

	return ll


def get_venues_categories(readCache=CacheOrGet):
	"""
	Returns a hierarchical list of categories applied to venues.
	"""
	response = foursquare_get("venues/categories", {}, readCache)
	if response:
		return response['response']['categories']


def venue_add(venue, ignoreDuplicates=False, ignoreDuplicatesKey=None):
	"""
	required: name, ll
	optional: address, crossStreet, city, state, zip, phone, twitter, primaryCategoryId, description, url
	second_run: ignoreDuplicates, ignoreDuplicatesKey
	"""
	response = foursquare_post("venues/add", venue)
	return response


def venues_venue(venueId, readCache=CacheIfPosible):
	response = foursquare_get("venues/" + venueId, {}, readCache)
	if response:
		#response > venue > tips > groups [] > items [] >
		return response['response']['venue']


def users_leaderboard(read_cache):
	response = foursquare_get("users/leaderboard", {}, read_cache)
	if response:
		return response['response']['leaderboard']['items']


def __delete_venue_with_tip(tipId):
	"""
	A nasty hack.  If a tip changes status in a venue, I uncache the venue, since
	the cached data is out-of-date, and manually synching this is pretty hard work
	This may change if future </lie>
	"""
	conn = sqlite3.connect(query_cache)
	conn.execute("DELETE FROM queries WHERE value LIKE ?", ("%" + tipId + "%",))
	conn.commit()
	conn.close()


def tip_add(venueId, text, url=""):
	broadcast = config_get("broadcast")
	if broadcast == None:
		broadcast = BROADCAST_DEFAULT

	response = foursquare_post("/tips/add", {'venueId': venueId, 'text': text, 'url': url, 'broadcast': broadcast})
	return response


def tip_marktodo(tipId, marked):
	if marked:
		response = foursquare_post("tips/" + tipId + "/marktodo", {})
	else:
		response = foursquare_post("lists/self/todos/deleteitem", {'itemId': tipId})
	__delete_venue_with_tip(tipId)
	return response


def tip_markdone(tipId, marked):
	if marked:
		response = foursquare_post("tips/" + tipId + "/markdone", {})
	else:
		response = foursquare_post("lists/self/dones/deleteitem", {'itemId': tipId})
	__delete_venue_with_tip(tipId)
	return response

def user_mayorships(userId, read_cache):
	response = foursquare_get("users/" + userId + "/mayorships", {}, read_cache)
	if response:
		return build_venue_array(response['response']['mayorships']['items'])

############################
# Extra one-time functions #
############################


def fetch_category_image(category):
	prefix = category['icon']['prefix']
	extension = category['icon']['name']
	image(prefix + "64" + extension)
	if 'categories' in category:
		for category in category['categories']:
			fetch_category_image(category)


def init_category_icon_cache():
	categories = get_venues_categories(ForceFetch)
	for category in categories:
		fetch_category_image(category)
	print "done updating image cache"


def init():
	authData['CODE'] = config_get("code")
	authData['ACCESS_TOKEN'] = config_get("access_token")

if __name__ == "__main__":
	print "This is the foursquare API library, yo're not supposed to run this!"
	sys.exit(0)
else:
	init()
