#!/usr/bin/env python

from setuptools import setup
from pkg_resources import WorkingSet , DistributionNotFound
working_set = WorkingSet()

requirements = ["watchdog>=0.8.0"]

try:
    working_set.require('paramiko>=1.10.0')
except DistributionNotFound:
    reqirements.append('paramiko>=1.10.0')

setup(name='FolderSync',
	version='0.1.0',
	description='Copy and modify directory content in various ways ',
	author='Luka Cehovin',
	author_email='luka.cehovin@gmail.com',
	url='https://github.com/lukacu/python-foldersync/',
	packages=['foldersync', 'foldersync.storage', 'foldersync.processors'],
	scripts=["bin/folderwatch", "bin/folderexport"],
    install_requires=requirements,
)
