# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os
import re
import shutil

from foldersync.processors import register_processor, Processor, Content

class LineBlocksProcessor(Processor):
  def __init__(self, data):
    self._exact = True
    if 'match' in data and data['match'] == 'contains':
      self._exact = False
    self._exclude = True
    if 'operation' in data and data['operation'] == 'include':
      self._exclude = False
    self._start = data['start']
    self._stop = data['stop']

  def process(self, content, context):

    text = content.get_text()

    filtered = []
    lines = text.splitlines()
    skipping = not self._exclude

    print self._exact

    for line in lines:
      if skipping:
        if (self._exact and line == self._stop) or (not self._exact and line.find(self._stop) > -1):
          skipping = False
      else:
        if (self._exact and line == self._start) or (not self._exact and line.find(self._start) > -1):
          skipping = True
        else:
          filtered.append(line)

    return Content(content.get_source(), text='\n'.join(filtered))

class LinesProcessor(Processor):
  def __init__(self, data):
    self._operation = 'exclude'
    if 'operation' in data and data['operation'] in ['exclude']:
      self._operation = data['operation']

    self._contains = []
    if 'contains' in data and type(data['contains']) == list:
      self._contains = data['contains']

  def process(self, content, context):

    text = content.get_text()

    filtered = []
    lines = text.splitlines()

    if self._operation == 'exclude':
      for line in lines:
        include = True
        for substr in self._contains:
          if line.find(substr) > -1:
            include = False
            break
        if include:
          filtered.append(line)
    else:
      filtered = lines

    return Content(content.get_source(), text='\n'.join(filtered))

class RegexProcessor(Processor):
  def __init__(self, data):
    self._pattern = re.compile(data['pattern'])
    self._replacement = data['replacement']

  def process(self, content, context):
    output_content = self._pattern.sub(self._replacement, content.get_text())
    return Content(content.get_source(), text=output_content)

register_processor('lines', LinesProcessor)
register_processor('lineblocks', LineBlocksProcessor)
register_processor('regex', RegexProcessor)
