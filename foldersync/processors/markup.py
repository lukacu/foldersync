# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os
import tempfile
import shutil

from foldersync.processors import register_processor, Processor, Content

class MarkdownProcessor(Processor):
  def __init__(self, data):
    from markdown import markdown
    self._markdown = markdown
    if data is dict:
      config = {k:v for (k,v) in data.iteritems() if k in ['extensions', 'extension_configs', 'output_format', 'safe_mode', 'html_replacement_text', 'tab_length', 'enable_attributes', 'smart_emphasis', 'lazy_ol']}
      self._config = config
    else:
      self._config = {}

  def process(self, content, context):

    text = content.get_text()
    html = self._markdown(text, **self._config)
    return Content(content.get_source(), text=html)

register_processor('markdown', MarkdownProcessor)


