# -*- coding: utf-8 -*-

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

from PySide.QtGui import QDesktopServices
from PySide.QtCore import QUrl
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urllib
import foursquare
try:
	import json
except ImportError:
	import simplejson as json
import re


class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		if re.match("^\\/auth\\?code\\=[0-9|A-Z]*$", self.path):
			code = re.sub("^\\/auth\\?code\\=", "", self.path)
			self.wfile.write("<h1>Cheers! The aplication has been authorized! You may now close this window.</h1>")
			foursquare.config_set("code", code)
		else:
			self.wfile.write("<h1>It looks like the foursquare response didn't have the code I expected.</h1>Please, report this bug to hugo@osvaldobarrera.com.ar.<p>")
			self.wfile.write("Response :<p><pre>" + self.path + "</pre>")


def fetch_token():
	code = foursquare.config_get("code")
	url = "https://foursquare.com/oauth2/access_token?client_id=" + foursquare.CLIENT_ID + "&client_secret=" + foursquare.CLIENT_SECRET + "&grant_type=authorization_code&redirect_uri=" + foursquare.CALLBACK_URI + "&code=" + code
	url = urllib.urlopen(url)
	response = url.read()
	response = json.loads(response, "UTF-8")
	foursquare.config_set("access_token", response['access_token'])
	foursquare.init()


def fetch_code():
	url = "https://foursquare.com/oauth2/authenticate?client_id=" + foursquare.CLIENT_ID + "&response_type=code&redirect_uri=" + foursquare.CALLBACK_URI + "&display=touch"
	QDesktopServices.openUrl(QUrl(url, QUrl.StrictMode))
	httpd = HTTPServer(("localhost", 6060), Handler)
	httpd.handle_request()
