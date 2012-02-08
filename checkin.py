#!/usr/bin/python2
import json
import urllib
import sys

CLIENT_ID="A0IJ0P4EFRO50JUEYALJDGR52RDS0O4H1OKPSIEYZ5LHSNGH"
CLIENT_SECRET="ACDUWAODBXRUPXHMVVWOXXATFN0PM0GP2PSLI5MZZCTUQ2TV"
CALLBACK_URL="http://localhost:6060/auth"

CODE="MFY3CM12JZHHSR43BJHTNN3C2ZIP3ZQRZNGA1CA35BH1NQMT"
ACCESS_TOKEN="GSMXQNPBOYRT3XM54FKK31EBABYWADDTKEUKNG42JNWQIZZX"

params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'group': "created"})
f = urllib.urlopen("https://api.foursquare.com/v2/users/self/venuehistory?%s" % params)

response = json.load(f,"UTF-8")
toprint = response[u'response'][u'venues']

venues = dict()
for item in response[u'response'][u'venues'][u'items']:
	venues[item[u'venue'][u'id']]=item[u'venue']

print venues.keys()
# for uid, venue in venues.iteritems():
# 	print venue[u'id']
# 	print venue[u'name']
# 	print venue[u'location'][u'lat']
# 	print venue[u'location'][u'lng']
# 	print ""


place="4b931a6df964a520483534e3"
print json.dumps(venues[place], sort_keys=True, indent=4)
venue = venues[place]

lat = "{0:2.8f}".format(float((ord(place[0]) + (ord(place[1])*100)))/(10000*10000) + venue[u'location'][u'lat'])
lng = "{0:2.8f}".format(float((ord(place[2]) + (ord(place[3])*100)))/(10000*10000) + venue[u'location'][u'lng'])
ll = lat + "," + lng

sys.exit()

params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'venueId': place, 'broadcast': "public,facebook", 'll': ll})
f = urllib.urlopen("https://api.foursquare.com/v2/checkins/add", params)

response = json.load(f,"UTF-8")
print json.dumps(response, sort_keys=True, indent=4)