#!/usr/bin/python2

import json

CLIENT_ID="A0IJ0P4EFRO50JUEYALJDGR52RDS0O4H1OKPSIEYZ5LHSNGH"
CLIENT_SECRET="ACDUWAODBXRUPXHMVVWOXXATFN0PM0GP2PSLI5MZZCTUQ2TV"
CALLBACK_URL="http://localhost:6060/auth"

CODE="MFY3CM12JZHHSR43BJHTNN3C2ZIP3ZQRZNGA1CA35BH1NQMT"

ACCESS_TOKEN="GSMXQNPBOYRT3XM54FKK31EBABYWADDTKEUKNG42JNWQIZZX"

import urllib
params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'group': "created"})
f = urllib.urlopen("https://api.foursquare.com/v2/users/self/venuehistory?%s" % params)

response = json.load(f,"UTF-8")

toprint = response[u'response'][u'venues']

venues = dict()

for item in response[u'response'][u'venues'][u'items']:
	venues[item[u'venue'][u'id']]=item[u'venue']

print venues.keys()

for uid, venue in venues.iteritems():
	print venue[u'id']
	print venue[u'name']
	print venue[u'location'][u'lat']
	print venue[u'location'][u'lng']
	print ""	

import sys
sys.exit()

place="4b931a6df964a520483534e3"
ll = "-34.5970,-58.4158"

params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'venueId': place, 'broadcast': "public,facebook", 'll': ll})
f = urllib.urlopen("https://api.foursquare.com/v2/checkins/add", params)

#print f.read()

response = json.load(f,"UTF-8")
print json.dumps(response, sort_keys=True, indent=4)