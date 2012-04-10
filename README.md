# UberSquare

Ubersquare is a foursquare application maemo, written in Python 2.5 using PySide.
Be warned that a great deal of the source could use *a lot* of refactoring, and probibly will be refactored at some point.

## Building

To build a .deb package you must follow two steps:

1. Run "python make.py" to prepare the necesary files.
2. You have two choices: submit the resulting files to the maemo extras autobuilder (and have the resulting package pushed to the extras-devel repo), or using debhelper.  Regrettably, debhelper is not available for maemo, so you'll need a Debian-based computer in order to do this.  Consult the maemo wiki for details on how to do this.

## Running

To run from source, just change to the ubersquare directory, and run "python gui.py".