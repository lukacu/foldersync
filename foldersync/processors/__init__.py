# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os
import tempfile
import codecs

processors = {}

class Content(object):
  def __init__(self, source, text = None, filename = None, metadata = {}):
#    if not content and not filename:
#      raise Exception('At least one argument shoud define content')
 
    if filename and not os.path.exists(filename):
      raise Exception('File does not exist: %s' % filename)

    if not source:
      raise Exception('Source must be a string')

    self._source = source
    self._content = text
    self._path = filename
    self._cleanup = False
    self._metadata = metadata

  def __del__(self):
    if self._path and self._cleanup and os.path.exists(self._path):
      os.unlink(self._path)

  def get_source(self):
    return self._source

  def get_metadata(self):
    return self._metadata

  def get_text(self):
    if self._content == None:
      fp = codecs.open(self._path, 'r', "utf-8")
      self._content = fp.read()
      fp.close()
    return self._content

  def get_filename(self):
    if not self._path:
      fp, self._path = tempfile.mkstemp()
      self._cleanup = True
      if self._content:
        os.write(fp, self._content.encode("utf-8"))
      os.close(fp)
    return self._path

class Processor(object):

  def process(self, content, context):
    return content

def register_processor(name, definition):
  processors[name] = definition

from . import codestyle, textfilter, matdoc, markup, templates

def create_processor(data):
  if not ("processor" in data):
    raise ValueError('Processor type not defined')

  name = data['processor']

  if name in processors:
    return processors[name](data)

  print "Warning: Processor '%s' not defined" % name
  return Processor()



