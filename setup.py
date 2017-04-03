#!/usr/bin/env python

from distutils.core import setup

setup(name='FolderSync',
	version='0.1.0',
	description='Copy and modify directory content in various ways ',
	author='Luka Cehovin',
	author_email='luka.cehovin@gmail.com',
	url='https://github.com/lukacu/python-foldersync/',
	packages=['foldersync', 'foldersync.storage', 'foldersync.processors'],
	scripts=["bin/folderwatch", "bin/folderexport"],
    requires=["watchdog", "paramiko", "ftplib"],
)
