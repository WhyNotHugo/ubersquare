#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
VERSION="0.3.3"

from distutils.core import setup
from subprocess import call
import os
import sys
import py2deb
import shutil

fakeargs = [sys.argv[0], "build", "bdist_dumb"]
sys.argv = fakeargs

try:
	os.chdir(os.path.dirname(sys.argv[0]))
except:
	pass

setup(name='ubersquare',
      version=VERSION,
      description='A foursquare client for maemo',
      url='http://ubertech.com.ar/square',
      author='Hugo Osvaldo Barrera',
      author_email='hugo@osvaldobarrera.com.ar',
      packages=['ubersquare', 'ubersquare.venues', 'ubersquare.checkins'],
      license='BSD'
)

shutil.rmtree("package/usr/lib")
call(["tar", "-C", "package/", "-xzf", "dist/ubersquare-" + VERSION + ".linux-armv7l.tar.gz"])
shutil.rmtree("build")
shutil.rmtree("dist")

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
version = VERSION
build = "1"
changeloginformation = open("CHANGES").read() 
dir_name = "package"
for root, dirs, files in os.walk(dir_name):
	real_dir = "/" + root[len(dir_name):]
	fake_file = []
	for f in files:
		fake_file.append(root + os.sep + f + "|" + f)
	if len(fake_file) > 0:
		p[real_dir] = fake_file
print p
r = p.generate(version,build,changelog=changeloginformation,tar=True,dsc=True,changes=True,build=False,src=True)

print "Done!"