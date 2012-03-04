#!/usr/bin/python2.5
# -*- coding: utf-8 -*-

import py2deb
import os
if __name__ == "__main__":
	try:
		os.chdir(os.path.dirname(sys.argv[0]))
	except:
		pass
	print
	p=py2deb.Py2deb("ubersquare")
	p.description="A foursquare client for maemo."
	p.author="Hugo Osvaldo Barrera"
	p.license="bsd"
	p.mail="hugo@osvaldobarrera.com.ar"
	p.depends = "python2.5, python-pyside, python-simplejson, python-xdg, python-location"
	p.section="user/navigation"
	#p.icon = "/home/user/MyDocs/mclock/mClock.png"
	p.arch="all"
	p.urgency="low"
	p.distribution="fremantle"
	p.repository="extras-devel"
	p.xsbc_bugtracker="http://bugs.maemo.org"
	version = "0.2.0"
	build = "1"
	changeloginformation = "Fixed dependencies" 
	dir_name = "src"
	for root, dirs, files in os.walk(dir_name):
		real_dir = "/" + root[len(dir_name):]
		fake_file = []
		for f in files:
			fake_file.append(root + os.sep + f + "|" + f)
		if len(fake_file) > 0:
			p[real_dir] = fake_file
	print p
	r = p.generate(version,build,changelog=changeloginformation,tar=True,dsc=True,changes=True,build=False,src=True)