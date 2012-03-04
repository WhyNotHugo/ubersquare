python setup.py build bdist_dumb &&
echo " * Deleting old files from package dir" &&
rm -rf package/src/usr/lib &&
echo " * unpacking new python modules into package dir" &&
tar -C package/src/ -xzf dist/ubersquare-0.2.0.linux-armv7l.tar.gz &&
echo " * deleting build/ and dist/" &&
rm -rf build dist &&
echo "Done!"
