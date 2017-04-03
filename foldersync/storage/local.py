#!/usr/bin/python
# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import sys
import os
import shutil

from foldersync.storage import Status

class LocalStorage(object):
  def __init__(self):
    pass

  def put(self, localpath, remotepath):
    if not os.path.exists(localpath):
      return
    if os.path.isdir(localpath):
      try:
        os.mkdir(remotepath)
      except IOError:
        pass
    else:
      shutil.copy(localpath, remotepath)

  def stat(self, remotepath):
    try:
      status = os.stat(remotepath)
      return Status(status.st_mtime, status.st_size)
    except OSError:
      return None

