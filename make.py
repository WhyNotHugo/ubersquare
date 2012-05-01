#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
VERSION="0.4.1"
BUILD="1"

from distutils.core import setup
from subprocess import call
import os
import sys
import py2deb
import shutil

PKGNAME = "ubersquare"
PKGDESC = "A foursquare client for maemo"

AUTHOR_NAME  = "Hugo Osvaldo Barrera"
AUTHOR_EMAIL = "hugo@osvaldobarrera.com.ar"

WEBSITE = "https://github.com/hobarrera/UberSquare"


####################################################
### Make setuptools pack this as a python module ###
####################################################

# Nasty hack to make setuptools belive it was called with these arguments
fakeargs = [sys.argv[0], "build", "bdist_dumb"]
sys.argv = fakeargs

os.chdir(os.path.dirname(sys.argv[0]))

setup(name         = PKGNAME,
      version      = VERSION,
      description  = PKGDESC,
      url          = WEBSITE,
      author       = AUTHOR_NAME,
      author_email = AUTHOR_EMAIL,
      packages     = ['ubersquare'],
      license      = 'BSD'
)

########################################################################################
### Prepare the files packed as a python modules to repack them into de .deb package ###
########################################################################################

shutil.rmtree("package/usr/lib")
call(["tar", "-C", "package/", "-xzf", "dist/" + PKGNAME + "-" + VERSION + ".linux-armv7l.tar.gz"])
shutil.rmtree("build")
shutil.rmtree("dist")

##########################################################################################
### Create files necesary to create a .deb package using the previously unpacked files ###
##########################################################################################

# TODO: modify version on the .desktop file (using ConfigParser would work)

print
p=py2deb.Py2deb(PKGNAME)
p.description=PKGDESC
p.author=AUTHOR_NAME
p.license="bsd"
p.mail=AUTHOR_EMAIL
p.depends = "python2.5, python-pyside, python-simplejson, python-xdg, python-location"
p.section="user/navigation"
p.icon = "/usr/share/icons/hicolor/26x26/apps/foursquare.png"
p.arch="all"
p.urgency="low"
p.distribution="fremantle"
p.repository="extras-devel"
p.xsbc_bugtracker="http://bugs.maemo.org"
dir_name = "package"
for root, dirs, files in os.walk(dir_name):
    real_dir = "/" + root[len(dir_name):]
    fake_file = []
    for f in files:
        fake_file.append(root + os.sep + f + "|" + f)
    if len(fake_file) > 0:
        p[real_dir] = fake_file
print p
p.generate(version      = VERSION,
           buildversion = BUILD,
           changelog    = open("CHANGES").read(),
           tar          = True,
           dsc          = True,
           changes      = True,
           build        = False,
           src          = True
)

print "Done!"