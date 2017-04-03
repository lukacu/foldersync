# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

"""
Friendly Python SSH2 interface.
Copied from http://media.commandline.org.uk//code/ssh.txt
Modified by James Yoneda to include command-line arguments.
"""

import getopt
import os
import time
import paramiko
import sys
import tempfile

from foldersync.storage import Status

class SSHStorage(object):
  """Connects and logs into the specified hostname. 
  Arguments that are not given are guessed from the environment.""" 

  def __init__(self,
         host,
         username = None,
         private_key = None,
         password = None,
         port = 22,
         ):

    if port == None:
      port = 22
    else:
      port = int(port);

    self._sftp_live = False
    self._sftp = None
    if not username:
      username = os.environ['LOGNAME']

    # Log to a temporary file.
    templog = tempfile.mkstemp('.txt', 'con-')[1]
    paramiko.util.log_to_file(templog)

    # Begin the SSH transport.
    self._transport = paramiko.Transport((host, port))
    self._tranport_live = True
    # Authenticate the transport.
    
    if password:
      # Using Password.
      self._transport.connect(username = username, password = password)
    else:
      ## Use Private Key.
      #if not private_key:
      #  # Try to use default key.
      #  if os.path.exists(os.path.expanduser('~/.con/id_rsa')):
      #    private_key = '~/.con/id_rsa'
      #  elif os.path.exists(os.path.expanduser('~/.con/id_dsa')):
      #    private_key = '~/.con/id_dsa'
      #  else:
      #    raise TypeError, "You have not specified a password or key."

      private_key_file = os.path.expanduser(private_key)
      rsa_key = paramiko.RSAKey.from_private_key_file(private_key_file)
      self._transport.connect(username = username, pkey = rsa_key)

    self._sftp_connect()
    self._time_offset = 0

    try:
      remote_time = int(self._execute("date +%s")[0].strip())
      self._time_offset = time.time() - remote_time
    except:
      pass

  def _sftp_connect(self):
    """Establish a SFTP connection."""
    if not self._sftp_live:
      self._sftp = paramiko.SFTPClient.from_transport(self._transport)
      self._sftp_live = True

  def put(self, localpath, remotepath = None):
    """Copies a file between the local host and the remote host."""
    if not remotepath:
      remotepath = os.path.split(localpath)[1]
    if not os.path.exists(localpath):
      return
    self._sftp_connect()
    if os.path.isdir(localpath):
      try:
        self._sftp.mkdir(remotepath)
      except IOError:
        pass
    else:
      self._sftp.put(localpath, remotepath)

  def stat(self, remotepath):
    """Provides information about the remote file."""
    self._sftp_connect()
    try:
      status = self._sftp.stat(remotepath)
      return Status(status.st_mtime + self._time_offset, status.st_size)
    except IOError:
      return None

  def _execute(self, command):
    """Execute a given command on a remote machine."""
    channel = self._transport.open_session()
    channel.exec_command(command)
    output = channel.makefile('rb', -1).readlines()
    if output:
      return output
    else:
      return channel.makefile_stderr('rb', -1).readlines()

  def _get(self, remotepath, localpath = None):
    """Copies a file between the remote host and the local host."""
    if not localpath:
      localpath = os.path.split(remotepath)[1]
    self._sftp_connect()
    self._sftp.get(remotepath, localpath)

  def close(self):
    """Closes the connection and cleans up."""
    # Close SFTP Connection.
    if self._sftp_live:
      self._sftp.close()
      self._sftp_live = False
    # Close the SSH Transport.
    if self._tranport_live:
      self._transport.close()
      self._tranport_live = False

  def __del__(self):
    """Attempt to clean up if not explicitly closed."""
    self.close()

