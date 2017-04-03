# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os
import copy

from jinja2.exceptions import TemplateNotFound
import jinja2

from foldersync.processors import register_processor, Processor, Content

class Jinja2Processor(Processor):
  def __init__(self, data):
    defaults = {'path' : ['.'], 'template' : 'base.tpl'}
    defaults.update(data)
    loader = jinja2.FileSystemLoader(defaults['path'])
    self._env = jinja2.Environment(loader=loader)
    self._env.globals['relative'] = Jinja2Processor._relative
    self._env.globals['basename'] = Jinja2Processor._basename
    self._env.globals['dirname'] = Jinja2Processor._dirname
    self._template = self._env.get_template(defaults['template'])
    self._context = {}
    if 'context' in data and type(data['context']) is dict:
      self._context.update(data['context'])

  @staticmethod
  def _relative(root, path):
    return os.path.relpath(path, root)

  @staticmethod
  def _basename(path):
    return os.path.basename(path)

  @staticmethod
  def _dirname(path):
    return os.path.dirname(path)

  def process(self, content, context):
    template_context = copy.deepcopy(self._context)
    template_context['context'] = context
    template_context['meta'] = content.get_metadata()
    template_context['content'] = content.get_text()
    output_content = self._template.render(template_context)

    return Content(content.get_source(), text=output_content)

register_processor('jinja2', Jinja2Processor)




