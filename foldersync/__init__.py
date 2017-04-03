# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import json
import os
import re
import fnmatch

def get_relative_path(root, path):
    """Returns the path of a file relative to the root."""
    root = os.path.abspath(root)
    path = os.path.abspath(path)
    if root[-1:] != os.sep:
        root += os.sep

    assert path.startswith(root)
    return path[len(root):]

def to_unix_path(path):
    return path.replace('\\', '/')

def to_win_path(path):
    return path.replace('/', '\\')

def unix_path_join(path1, path2):
    """Like os.path.join(), but not OS dependent (unix only)."""
    if path1[-1:] != '/' and len(path1) > 0:
        path1 += '/'
    if path2[:1] == '/':
        path2 = path2[1:]
    return path1 + path2


class Entry:
  """Keeps track of the modification time of a file and processing."""
  def __init__(self, filename):
    self.filename = filename
    self.date_modified = os.stat(self.filename).st_mtime
    self.size = os.stat(self.filename).st_size
    self.digest = None

    self.has_changed_locally()

  def has_changed_locally(self):

    date_modified = os.stat(self.filename).st_mtime

    if date_modified != self.date_modified:
      self.date_modified = date_modified
      return True
    else:
      return False

class FolderSync(object):

  def __init__(self, storage, local_folder, remote_folder, force_update=False):
    self._entries = {}
    self._ignore = []
    self._local_folder = local_folder
    self._remote_folder = remote_folder
    self._storage = storage 
    self._force_update = force_update
    self._first_scan = True

  def _put_file(self, entry):
    filename_rel = get_relative_path(self._local_folder, entry.filename)
    filename_rel = to_unix_path(filename_rel)
    remote_filename = self._get_remote_path(entry)
    if os.path.isdir(entry.filename):
        print '[%s] Creating "%s" ...' % (self._local_folder, filename_rel)
    else:
        print '[%s] Copying "%s" ...' % (self._local_folder, filename_rel)
    self._storage.put(entry.filename, remote_filename)

  def _get_remote_path(self, entry):
    filename_rel = get_relative_path(self._local_folder, entry.filename)
    filename_rel = to_unix_path(filename_rel)
    return unix_path_join(self._remote_folder, filename_rel)

  def _check_remote_file(self, entry): 
    remote_filename = self._get_remote_path(entry)
    status = self._storage.stat(remote_filename)

    if status and os.path.isdir(entry.filename):
      return True 

    if not status:
      return False
    if status.date_modified and status.date_modified < entry.date_modified:
      return False
    return True 

  def _scan_entry(self, filename_full):

    filename_rel = get_relative_path(self._local_folder, filename_full)

    if filename_full in self._entries:      
      if self._entries[filename_full].has_changed_locally():
        self._put_file(self._entries[filename_full]) 
    elif self._first_scan:
      # New file, add it.
      self._entries[filename_full] = Entry(filename_full)
      if self._force_update or not self._check_remote_file(self._entries[filename_full]):
        self._put_file(self._entries[filename_full]) 

  def scan(self):
    """Scan a local folder, copy any changed/new files."""
    for dirpath, dirnames, filenames in os.walk(self._local_folder):
      for dirname in dirnames[:]:
        self._scan_entry(os.path.join(dirpath, dirname))
#        dirname_rel = get_relative_path(self._local_folder, dirname_full)
#        if self._must_ignore(dirname_rel):
#          dirnames.remove(dirname)
#        else:
#          if not dirname_full in self._folders:
#            if self._force_update or not self._check_folder(dirname_full):
#              self._put_file(dirname_full)
#            self._folders[dirname_full] = True

      for filename in filenames:
        # Check all files in the local folder.
        self._scan_entry(os.path.join(dirpath, filename))
          
    if self._force_update:
      self._force_update = False

    if self._first_scan:
      self._first_scan = False


