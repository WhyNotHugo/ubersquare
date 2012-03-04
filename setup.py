from distutils.core import setup

setup(name='ubersquare',
      version='0.2.0',
      #py_modules=['ubersquare'],
      description='A foursquare client for maemo',
      url='http://ubertech.com.ar/square',
      author='Hugo Osvaldo Barrera',
      author_email='hugo@osvaldobarrera.com.ar',
      packages=['ubersquare', 'ubersquare.venues', 'ubersquare.checkins'],
      license='BSD'
)
