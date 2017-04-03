# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
# based on matdocparser.py by Andrea Vedaldi
# Copyright (C) 2014-15 Andrea Vedaldi.
# All rights reserved.
#
# This file is part of the VLFeat library and is made available under
# the terms of the BSD license (see the COPYING file).

"""
MatDocParser is an interpreter for the MatDoc format. This is a simplified and
stricter version of Markdown suitable to commenting MATLAB functions. the format
is easily understood from an example:

A paragraph starts on a new line.
And continues on following lines.

Indenting with a whitespace introduces a verbatim code section:

   Like this
    This continues it

Different paragraphs are separated by blank lines.

* The *, -, + symbols at the beginning of a line introduce a list.
  Which can be continued on follwing paragraphs by proper indentation.

  Multiple paragraphs in a list item are also supported.

* This is the second item of the same list.

It is also possible to have definition lists such as

Term1:: Short description 2
   Longer explanation.

   Behaves like a list item.

Term2:: Short description 2
Term3:: Short description 3
  Longer explanations are optional.
"""

import sys
import os
import re
import codecs

from foldersync.processors import register_processor, Processor, Content

class ParseError(ValueError):
    pass

# --------------------------------------------------------------------
# Input line types (terminal symbols)
# --------------------------------------------------------------------

# Terminal symbols are organized in a hierarchy. Each line in the
# input document is mapped to leaf in this hierarchy, representing
# the type of line detected.

class Symbol(object):
    indent = None
    def isa(self, classinfo, indent = None):
        return isinstance(self, classinfo) and \
            (indent is None or self.indent == indent)
    def __str__(self, indent = 0):
        if self.indent is not None: x = "%d" % self.indent
        else: x = "*"
        return " "*indent + "%s(%s)" % (self.__class__.__name__, x)

# Terminal symbols
# Note that PL, BH, DH are all subclasses of L; the fields .text and .indent
# have the same meaning for all of them.
class Terminal(Symbol): pass
class EOF (Terminal): pass # end-of-file
class B (Terminal): pass # blank linke
class L (Terminal): # non-empty line: '<" "*indent><text>'
    text = ""
    def __str__(self, indent = 0):
        return "%s: %s" % (super(L, self).__str__(indent), self.text)
class PL (L): pass # regular line
class BH (L): # bullet: a line of type '  * <inner_text>'
    inner_indent = None
    inner_text = None
    bullet = None
class DH (L):  # description: a line of type ' <description>::<inner_text>'
    inner_text = None
    description = None

# A lexer object: parse lines of the input document into terminal symbols
class Lexer(object):
    def __init__(self, lines):
        self.lines = lines
        self.pos = -1

    def next(self):
        self.pos = self.pos + 1
        # no more
        if self.pos > len(self.lines)-1:
            x = EOF()
            return x
        line = self.lines[self.pos]
        # a blank line
        match = re.match(r"\s*\n?$", line) ;
        if match:
            return B()
        # a line of type '  <content>::<inner_text>'
        match = re.match(r"(\s*)(.*)::(.*)\n?$", line)
        if match:
            x = DH()
            x.indent = len(match.group(1))
            x.description = match.group(2)
            x.inner_text = match.group(3)
            x.text = x.description + "::" + x.inner_text
            return x
        # a line of type '  * <inner_contet>'
        match = re.match(r"(\s*)([-\*+]\s*)(\S.*)\n?$", line)
        if match:
            x = BH()
            x.indent = len(match.group(1))
            x.bullet = match.group(2)
            x.inner_indent = x.indent + len(x.bullet)
            x.inner_text = match.group(3)
            x.text = x.bullet + x.inner_text
            return x
        # a line of the type  '   <content>'
        match = re.match(r"(\s*)(\S.*)\n?$", line)
        if match:
            x = PL()
            x.indent = len(match.group(1))
            x.text = match.group(2)
            return x

# --------------------------------------------------------------------
# Non-terminal
# --------------------------------------------------------------------

# DIVL is a consecutive list of blocks with the same indent and/or blank
# lines.
#
# DIVL(indent) -> (B | P(indent) | V(indent) | BL(indent) | DL(indent))+
#
# A P(indent) is a paragraph, a list of regular lines indentent by the
# same amount.
#
# P(indent) -> PL(indent)+
#
# A V(indent) is a verbatim (code) block. It contains text lines and blank
# lines that have indentation strictly larger than indent:
#
# V(indent) -> L(i) (B | L(j), j > indent)+, for all i > indent
#
# A DL(indent) is a description list:
#
# DL(indent) -> DH(indent) DIVL(i)*,  i > indent
#
# A BL(indent) is a bullet list. It contains bullet list items, namely
# a sequence of special DIVL_BH(indent,inner_indent) whose first block
# is a paragaraph P_BH(indent,inner_indent) whose first line is a
# bullet header BH(indent,innner_indent). Here the bullet identation
# inner_indent is obtained as the inner_indent of the
# BH(indent,inner_indent) symbol. Formalising this with grammar rules
# is verbose; instead we use the simple `hack' of defining
#
# BL(indent) -> (DIVL(inner_indent))+
#
# where DIVL(inner_indent) are regular DIVL, obtaine after replacing
# the bullet header line BH with a standard paragraph line PL.

class NonTerminal(Symbol):
    children = []
    def __init__(self, *args):
        self.children = list(args)
    def __str__(self, indent = 0):
        s = " "*indent + super(NonTerminal, self).__str__() + "\n"
        for c in self.children:
            s += c.__str__(indent + 2) + "\n"
        return s[:-1]

class DIVL(NonTerminal): pass
class DIV(NonTerminal): pass
class BL(NonTerminal): pass
class DL(NonTerminal): pass
class DI(NonTerminal): pass
class P(DIV): pass
class V(DIV): pass

# --------------------------------------------------------------------
class Parser(object):
    lexer = None
    stack = []
    lookahead = None

    def shift(self):
        if self.lookahead:
            self.stack.append(self.lookahead)
        self.lookahead = self.lexer.next()

    def reduce(self, S, n, indent = None):
        #print "reducing %s with %d" % (S.__name__, n)
        s = S(*self.stack[-n:])
        del self.stack[-n:]
        s.indent = indent
        self.stack.append(s)
        return s

    def parse(self, lexer):
        self.lexer = lexer
        self.stack = []
        while True:
            self.lookahead = self.lexer.next()
            if not self.lookahead.isa(B): break
        self.parse_DIVL(self.lookahead.indent)
        return self.stack[0]

    def parse_P(self, indent):
        i = 0
        if indent is None: indent = self.lookahead.indent
        while self.lookahead.isa(PL, indent):
            self.shift()
            i = i + 1
        self.reduce(P, i, indent)

    def parse_V(self, indent):
        i = 0
        while (self.lookahead.isa(L) and self.lookahead.indent > indent) or \
              (self.lookahead.isa(B)):
            self.shift()
            i = i + 1
        self.reduce(V, i, indent)

    def parse_DIV_helper(self, indent):
        if self.lookahead.isa(PL, indent):
            self.parse_P(indent)
        elif self.lookahead.isa(L) and (self.lookahead.indent > indent):
            self.parse_V(indent)
        elif self.lookahead.isa(BH, indent):
            self.parse_BL(indent)
        elif self.lookahead.isa(DH, indent):
            self.parse_DL(indent)
        elif self.lookahead.isa(B):
            self.shift()
        else:
            return False
        # leaves with B, P(indent), V(indent), BL(indent) or DL(indent)
        return True

    def parse_BI_helper(self, indent):
        x = self.lookahead
        if not x.isa(BH, indent): return False
        indent = x.inner_indent
        self.lookahead = PL()
        self.lookahead.text = x.inner_text
        self.lookahead.indent = indent
        self.parse_DIVL(indent)
        # leaves with DIVL(inner_indent) where inner_indent was
        # obtained from the bullet header symbol
        return True

    def parse_BL(self, indent):
        i = 0
        while self.parse_BI_helper(indent): i = i + 1
        if i == 0: raise ParseError("Error")
        self.reduce(BL, i, indent)

    def parse_DI_helper(self, indent):
        if not self.lookahead.isa(DH, indent): return False
        self.shift()
        if self.lookahead.indent > indent:
            self.parse_DIVL(self.lookahead.indent)
            self.reduce(DI, 2, indent)
        else:
            self.reduce(DI, 1, indent)
        return True

    def parse_DL(self, indent):
        i = 0
        while self.parse_DI_helper(indent): i = i + 1
        if i == 0: raise ParseError("Error")
        self.reduce(DL, i, indent)

    def parse_DIVL(self, indent = None):
        i = 0
        while self.parse_DIV_helper(indent):
            if indent is None: indent = self.stack[-1].indent
            i = i + 1
        self.reduce(DIVL, i, indent)

class Frame(object):
    prefix = ""
    before = None
    def __init__(self, prefix, before = None):
        self.prefix = prefix
        self.before = before

class Context(object):

  def __init__(self):
    self.frames = []
    self.lines = []

  def __str__(self):
      text =  ""
      for f in self.frames:
          if not f.before:
              text = text + f.prefix
          else:
              text = text + f.prefix[:-len(f.before)] + f.before
              f.before = None
      return text

  def pop(self):
    f = self.frames[-1]
    del self.frames[-1]
    return f

  def push(self, frame):
    self.frames.append(frame)

  def append(self, line=None):
    if line == None:
      self.lines.append(self.__str__())
    else:
      self.lines.append(line)


class MatDocProcessor(Processor):
  def __init__(self, data):
    pass

  def process(self, content, context):

    text = content.get_text()

    (body, func, brief) = self._extract(text.splitlines())
    parser = Parser()
    lexer = Lexer(body)
    tree = parser.parse(lexer)
    lines = MatDocProcessor._render(func, brief, tree)

    (root, ext) = os.path.splitext(content.get_source())

#    metadata = content.get_metadata()
#    metadata['function']

    return Content(content.get_source(), text='\n'.join(lines))

  def _extract(self, lines):
    body         = []
    func         = ""
    brief        = ""
    seenfunction = False
    seenpercent  = False

    for l in lines:
        line = l.strip().lstrip()
        if line.startswith('%'): seenpercent = True
        if line.startswith('function'):
            seenfunction = True
            continue
        if not line.startswith('%'):
            if (seenfunction and seenpercent) or not seenfunction:
                break
            else:
                continue
        # remove leading `%' character
        line = line[1:] #
        body.append('%s\n' % line)
    # Extract header from body
    if len(body) > 0:
        head  = body[0]
        body  = body[1:]
        match = re.match(r"^\s*(\w+)\s*(\S.*)\n$", head)
        if match:
          func  = match.group(1)
          brief = match.group(2)
        else:
          func  = ""
          brief = ""
    return (body, func, brief)

  @staticmethod
  def _render_L(tree, context):
      context.append("%s%s" % (context,tree.text))

  @staticmethod
  def _render_DH(tree, context):
      context.append("%s**%s** [*%s*]" % (context, tree.description.strip(), tree.inner_text.strip()))

  @staticmethod
  def _render_DI(tree, context):
      context.push(Frame("    ", "*   "))
      MatDocProcessor._render_DH(tree.children[0], context)
      context.append()
      if len(tree.children) > 1:
          MatDocProcessor._render_DIVL(tree.children[1], context)
      context.pop()

  @staticmethod
  def _render_DL(tree, context):
      for n in tree.children: MatDocProcessor._render_DI(n, context)

  @staticmethod
  def _render_P(tree, context):
      for n in tree.children: MatDocProcessor._render_L(n, context)
      context.append()

  @staticmethod
  def _render_B(tree, context):
      context.append()

  @staticmethod
  def _render_V(tree, context):
      context.push(Frame("    "))
      for n in tree.children:
          if n.isa(L): MatDocProcessor._render_L(n, context)
          elif n.isa(B): MatDocProcessor._render_B(n, context)
      context.pop()

  @staticmethod
  def _render_BL(tree, context):
    for n in tree.children:
      context.push(Frame("    ", "+   "))
      MatDocProcessor._render_DIVL(n, context)
      context.pop()

  @staticmethod
  def _render_DIVL(tree, context):
    for n in tree.children:
      if n.isa(P): MatDocProcessor._render_P(n, context)
      elif n.isa(BL): MatDocProcessor._render_BL(n, context)
      elif n.isa(DL): MatDocProcessor._render_DL(n, context)
      elif n.isa(V): MatDocProcessor._render_V(n, context)
      context.before = ""

  @staticmethod
  def _render(func, brief, tree):
    lines = ["## Function %s" % func, "### %s" % brief] 
    context = Context()
    MatDocProcessor._render_DIVL(tree, context)
    lines.extend(context.lines)
    return lines


METHOD_RE = re.compile(" *function +(?P<name>[a-zA-Z0-9_]+) *(\\((?P<argin>[^\\)]*)\\))? *(%.*)?$")
FUNCTION_RE = re.compile(" *function +(?P<argout>[a-zA-Z0-9_]+) *=? *(?P<name>[a-zA-Z0-9_]+) *(\\((?P<argin>[^\\)]*)\\))? *(%.*)?$")
FUNCTION2_RE = re.compile(" *function +\\[(?P<argout>[^\\]]*)\\] *=? *(?P<name>[a-zA-Z0-9_]+) *(\\((?P<argin>[^\\)]*)\\))? *(%.*)?$")

class MatlabAutoDocumentationProcessor(Processor):
  def __init__(self, data):
    pass

  def process(self, content, context):
    modified = []
    text = content.get_text()
    lines = text.splitlines()

    pending = None

    for line in lines:
      obj = MatlabAutoDocumentationProcessor.parse_header(line)

      if obj["type"] == "function":
        pending = obj
      elif not obj["type"] == "comment" and pending: 
        modified.extend(MatlabAutoDocumentationProcessor.document_header(pending))
        pending = None
      else:
        pending = None

      modified.append(line)

    if len(text) > 0 and text[-1] == '\n':
      modified.append("")

    return Content(content.get_source(), text='\n'.join(modified))

  @staticmethod
  def parse_header(line):
    line = line.lstrip()

    if len(line) == 0:
      return {'type': 'empty'}

    if line[0] == '%':
      return {'type': 'comment'}

    match = METHOD_RE.match(line)
    if match:
      argin = [s.strip() for s in match.group('argin').split(',')] if match.group('argin') else []
      return {'type': 'function', 'name' : match.group('name'), 'argout' : [], 'argin' : argin}
    match = FUNCTION_RE.match(line)
    if match:
      argout = [s.strip() for s in match.group('argout').split(',')] if match.group('argout') else []
      argin = [s.strip() for s in match.group('argin').split(',')] if match.group('argin') else []
      return {'type': 'function', 'name' : match.group('name'), 'argout' : argout, 'argin' : argin}
    match = FUNCTION2_RE.match(line)
    if match:
      argout = [s.strip() for s in match.group('argout').split(',')] if match.group('argout') else []
      argin = [s.strip() for s in match.group('argin').split(',')] if match.group('argin') else []
      return {'type': 'function', 'name' : match.group('name'), 'argout' : argout, 'argin' : argin}

    return {'type': 'instruction'}

  @staticmethod
  def document_header(header):
    if header["type"] == "function":
      doc = []
      doc.append("%% %s <short description>" % header["name"])
      doc.append("%")
      doc.append("% <long description>")
      doc.append("%")
      if len(header["argin"]) > 0:
        doc.append("% Input:")
        for arg in header["argin"]:
          doc.append("%% - %s (<type>): <description>" % arg)
        doc.append("%")
      if len(header["argout"]) > 0:
        doc.append("% Output:")
        for arg in header["argout"]:
          doc.append("%% - %s (<type>): <description>" % arg)
        doc.append("%")
      doc.append("")
      return doc

    else:
      return []

register_processor('matlab.autodoc', MatlabAutoDocumentationProcessor)
register_processor('matdoc', MatDocProcessor)





