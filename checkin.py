#!/usr/bin/python2
import json
import urllib
import sys

CLIENT_ID="A0IJ0P4EFRO50JUEYALJDGR52RDS0O4H1OKPSIEYZ5LHSNGH"
CLIENT_SECRET="ACDUWAODBXRUPXHMVVWOXXATFN0PM0GP2PSLI5MZZCTUQ2TV"
CALLBACK_URL="http://localhost:6060/auth"

CODE="MFY3CM12JZHHSR43BJHTNN3C2ZIP3ZQRZNGA1CA35BH1NQMT"
ACCESS_TOKEN="GSMXQNPBOYRT3XM54FKK31EBABYWADDTKEUKNG42JNWQIZZX"

BASE_URL="https://api.foursquare.com/v2/"

def get_history():
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'group': "created"})
	f = urllib.urlopen("{}/users/self/venuehistory?{}".format(BASE_URL, params))
	response = json.load(f,"UTF-8")

	venues = dict()
	for item in response[u'response'][u'venues'][u'items']:
		venues[item[u'venue'][u'id']]=item[u'venue']

	return venues

def get_venue(venueId):
	params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'group': "created"})
	f = urllib.urlopen("{}/venues/{}?{}".format(BASE_URL, venueId, params))	
	response = json.load(f,"UTF-8")

	venue = response[u'response'][u'venue']

	return venue



venueId = "4b931a6df964a520483534e3"
venue = get_venue(venueId)
print json.dumps(venue[u'location'], sort_keys=True, indent=2)




#venue = venues[venueId]

lat = "{0:2.8f}".format(float((ord(venueId[0]) + (ord(venueId[1])*100)))/(10000*10000) + venue[u'location'][u'lat'])
lng = "{0:2.8f}".format(float((ord(venueId[2]) + (ord(venueId[3])*100)))/(10000*10000) + venue[u'location'][u'lng'])
ll = lat + "," + lng

sys.exit()

params = urllib.urlencode({'oauth_token': ACCESS_TOKEN, 'v': "20120208", 'venueId': venueId, 'broadcast': "public,facebook", 'll': ll})
f = urllib.urlopen("https://api.foursquare.com/v2/checkins/add", params)

response = json.load(f,"UTF-8")
print json.dumps(response, sort_keys=True, indent=4)