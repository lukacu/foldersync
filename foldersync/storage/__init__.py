# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os
import re
import getpass

URI_REGEX = { 'ssh' : re.compile('ssh://(?P<auth>[^@]+)@(?P<hostname>[^/:]+)(:(?P<port>[0-9]+))?(?P<path>/.*)'),
  'ftp' : re.compile('ftp://(?P<auth>[^@]+)@(?P<hostname>[^/:]+)(?P<port>:[0-9]+)?(?P<path>/.*)'),
  'dummy' : re.compile('dummy://'),
  'local' : re.compile('(?P<path>/.*)')
}

AUTH_REGEX = re.compile('(?P<username>[^:\\[]+)((:(?P<password>.*))|(\\[(?P<keyfile>[^\\]]*)\\]))?')
#AUTH_REGEX = re.compile('(?P<username>[^:\\[]+)\\[(?P<keyfile>[^\\]]*)\\]')


class DummyStorage:
  def __init__(self):
    pass

  def put(self, filename_full, remote_filename):
    pass

  def stat(self, remotepath):
    return None

class Status:
  def __init__(self, date_modified=None, size=None, digest=None):
    self.date_modified = date_modified
    self.size = size
    self.digest = digest

def parse_auth(auth, interactive=True):
  m = AUTH_REGEX.match(auth)
  if not m:
    raise Exception('Illegal authentication specification')

  auth = {'username' : m.group('username'),
          'password' : m.group('password'),
          'keyfile' : m.group('keyfile') }

  if interactive and auth['username'] is None:
    auth['username'] = raw_input("Enter username: ")

  if interactive and auth['password'] is None and auth['keyfile'] is None:
    auth['password'] = getpass.getpass("Enter password: ")

  return auth

from . import ssh, ftp, local


def create_storage(uri, interactive=True):

  for protocol, regex in URI_REGEX.items():
    m = regex.match(uri)
    if not m:
      continue

    if protocol == 'local':
      return local.LocalStorage(), os.path.abspath(uri)
    elif protocol == 'ftp':
      m = m.groupdict(None)
      auth = parse_auth(m['auth'])
      return ftp.FTPStorage(host=m['hostname'], username=auth['username'], password=auth['password'], port=m['port']), m['path']
    elif protocol == 'dummy':
      return DummyStorage(), '/'
    else:
      auth = parse_auth(m.group('auth'))
      return ssh.SSHStorage(host=m.group('hostname'), username=auth['username'], password=auth['password'], private_key=auth['keyfile'], port=m.group('port')), m.group('path')

  raise Exception('Illegal authentication specification')



