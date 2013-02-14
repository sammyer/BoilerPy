import os
from distutils.core import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
	name = "boilerpy",
	version = "1.0",
	author = "Sam Myer",
	author_email = "mail@frozencavemanmedia.com",
	description = "Python port of Boilerpipe, Boilerplate Removal and Fulltext Extraction from HTML pages",
	license = "Apache 2.0",
	keywords = "boilerpipe fulltext extraction",
	url = "https://github.com/sammyer/BoilerPy",
	packages=['boilerpy'],
	long_description=read('README.txt'),
	classifiers=[
		"Development Status :: 4 - Beta",
		"Topic :: Utilities",
		"License :: OSI Approved :: Apache License",
	]
)