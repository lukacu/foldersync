# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os
import tempfile
import shutil

from foldersync.processors import register_processor, Processor, Content

LANGUAGES = { ".c" : "C", ".h" : "C", ".cpp" : "C++", ".hpp" : "C++", ".java" : "Java", ".py" : "Python" }

def split_comments(lines, line_start=None, block_start=None, block_end=None):

  extract_comments



def language_from_extension(filename):
  ext = os.path.splitext(filename)[1].lower()

  if ext in LANGUAGES:
    return LANGUAGES[ext]

  return None


class AStyleProcessor(Processor):
  def __init__(self, data):
    self._arguments = []
    if 'arguments' in data and type(data['arguments']) == list:
      self._arguments = data['arguments']  

  def process(self, content, context):
    try:
      result = Content(content.get_source())
      #print 'astyle %s < "%s" > "%s"' % (" ".join(self._arguments), content.get_filename(), result.get_filename())
      os.system('astyle %s < "%s" > "%s"' % (" ".join(self._arguments), content.get_filename(), result.get_filename()))
      return result
    except OSError as e:
      if e.errno == os.errno.ENOENT:
        print "AStyle not installed on the system"
        return content
      else:
        raise

class LicenseProcessor(Processor):
  def __init__(self, data):
    if 'source' in data:
      fp = open(data['source'], 'r')
      self._license = fp.read()
      fp.close()

    if 'abort' in data:
      self._abort = data['abort']
    else:
      self._abort = []

  def process(self, content, context):

    language = language_from_extension(content.get_source())
   
    if not language:
      return content

    text = content.get_text()

    if language == 'Python':
      license = '# ' + self._license.replace('\n', '\n# ')
    else:
      width = max([len(line) for line in self._license.split('\n')])
      border = '*' * width
      license = '/' + border + '\n* ' + self._license.replace('\n', '\n* ') + '\n' + border + '/'

    return Content(content.get_source(), text=license + '\n' + text)



register_processor('astyle', AStyleProcessor)
register_processor('license', LicenseProcessor)

