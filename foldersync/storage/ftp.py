# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import sys
import os
from ftplib import FTP

from foldersync.storage import Status

class FTPStorage(object):
	def __init__(self, host, port=21, username=None, password=None):
    self.con = FTP()
    self.con.connect(host, port)

    if username is None:
	    username = ''
    if password is None:
	    password = ''

    self._time_offset = 0

    self.con.login(username, password)
	
	def put(self, localpath, remotepath = None):
    if os.path.isdir(localpath):
      try:
        self.con.mkd(remotepath)
      except:
        pass
    else:
      f = open(localpath, 'rb')
      self.con.storbinary('STOR %s' % remotepath, f)
      f.close()

	def stat(self, remotepath):
    try:
      time = int(self.con.sendcmd('MDTM %s' % remotepath))
      size = self.con.size(remotepath)

      return Status(time + self._time_offset, size)
    except:
      return None

  def close(self):
    self.con.quit()
