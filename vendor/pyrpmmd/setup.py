#!/usr/bin/env python

from setuptools import setup

setup(
	name='pyrpmmd',
	version='0.1.1',
	license='GPLv2+',
	description='Python module for reading rpm-md repo data',
	keywords='rpm-md rpmmd repomd yum rpm',
	# From https://pypi.python.org/pypi?%3Aaction=list_classifiers
	classifiers=[
		# Development status
		'Development Status :: 4 - Beta',
		# Target audience
		'Intended Audience :: Developers',
		# Type of software
		'Topic :: System :: Software Distribution',
		# License (must match license field)
		'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
		# Operating systems supported
		'Operating System :: OS Independent',
		# Supported Python versions
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 3',
		],
	author='Neal Gompa',
	author_email='ngompa@fedoraproject.org',
	url='https://pagure.io/pyrpmmd',
	packages=['rpmmd'],
	install_requires=[
		'six',
		],
)
