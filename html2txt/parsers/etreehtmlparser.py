import os
import re
import html5lib
import xml

import html
from html.parser import HTMLParser
from xml.etree import ElementTree

from collections import OrderedDict

from html5lib.treebuilders import getTreeBuilder

from .xmlfragmentparser import XmlFragmentParser

from .common import escape_url, escape_html

class ScopeNode:
  def __init__(self, uri, tag):
    self.nameTuple = (uri, tag)

def escape_attribute_characters(s):
  result = ''
  in_quote = False
  quote_char = None
  for c in s:
    if in_quote == True and c == quote_char:
      in_quote = False
    elif c == '"' or c == "'":
      if in_quote == False:
        in_quote = True
        quote_char = c
    if c == '<' and in_quote == True:
      c = '&lt;'
    elif c == '>' and in_quote == True:
      c = '&gt;'
    elif c == '&' and in_quote == True:
      c = '&amp;'
    result += c
  return result

def merge_dicts(*dict_args):
  """
  Given any number of dicts, shallow copy and merge into a new dict,
  precedence goes to key value pairs in latter dicts.
  """
  result = {}
  for dictionary in dict_args:
      result.update(dictionary)
  return result

#
# MIT License
#
# https://opensource.org/licenses/MIT
#
# Copyright 2020 Rene Sugar
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

class ETreeHTMLParser(HTMLParser):
  def __init__(self, namespaceHTMLElements=True):
    super(ETreeHTMLParser, self).__init__()
    tree = getTreeBuilder("etree")
    self.tree = tree(namespaceHTMLElements)
    self.tree.insertRoot({"name": "DOCUMENT_ROOT", "data": {}})
    # Assume HTML element is the root (e.g. parsing an HTML fragment or document)
    self.default_namespace_map_ = {
      "html": "http://www.w3.org/1999/xhtml",
      "mathml": "http://www.w3.org/1998/Math/MathML",
      "svg": "http://www.w3.org/2000/svg",
      "xlink": "http://www.w3.org/1999/xlink",
      "namespace": "http://www.w3.org/XML/1998/namespace",
      "xmlns": "http://www.w3.org/2000/xmlns/"
    }
    self.namespace_root_ = [
      '{http://www.w3.org/1999/xhtml}html',
      '{http://www.w3.org/2000/svg}svg',
      '{http://www.w3.org/1998/Math/MathML}math',
    ]
    self.namespace_map_ = [dict(self.default_namespace_map_)]
    self.default_namespace_ = ["http://www.w3.org/1999/xhtml"]
    self.all_namespaces_map_ = {}

  def namespace_uri_map(self):
    self.all_namespaces_map_.update(self.default_namespace_map_)
    return self.all_namespaces_map_

  def namespace_prefix_map(self):
    return {v: k for k, v in self.all_namespaces_map_.items()}

  def default_namespace(self):
    return self.default_namespace_[-1]

  def push_default_namespace(self, namespace):
    self.default_namespace_.append(namespace)

  def pop_default_namespace(self):
    if len(self.default_namespace_) > 1:
      return self.default_namespace_.pop()
    return self.default_namespace_[-1]

  def getFragment(self):
    return self.tree.getFragment()

  def push_namespace(self):
    self.namespace_map_.append({})

  def pop_namespace(self):
    if len(self.namespace_map_) > 1:
      nd = self.namespace_map_.pop()
      self.all_namespaces_map_.update(nd)
      return nd
    nd = self.namespace_map_[-1]
    self.all_namespaces_map_.update(nd)
    return nd

  def get_namespace(self, name):
    # '{http://www.w3.org/1999/xhtml}{http://www.w3.org/2000/svg}svg'
    if name[0] == "{":
      name_part = name.split("{")[-1]
      uri, tag = name_part.split("}")
      return (uri, tag)
    else:
      return (None, name)

  def update_namespace(self, prefix, uri):
    if prefix is None:
      prefix = uri.split('/')[-1].lower()
      if prefix == 'xhtml':
        prefix = 'html'
    if uri in self.namespace_map_[-1]:
      if prefix != self.namespace_map_[-1][uri]:
        # NOTE: Several namespaces are preloaded with the preferred prefix
        raise ValueError("Prefix changed for namespace URI")
      return (prefix, uri)
    self.namespace_map_[-1][uri] = prefix
    return (prefix, uri)

  def get_namespace_uri(self, prefix):
    count = len(self.namespace_map_) + 1
    for i in range(-1, 0 - count, -1):
      if prefix in self.namespace_map_[i]:
        return self.namespace_map_[i][prefix]
    return None

  def elementInScope(self, uri, tag):
    found = False
    for node in reversed(self.tree.openElements):
      if ScopeNode(uri, tag).nameTuple == node.nameTuple:
        found = True
    return found

  def handle_starttag(self, tag, attrs):
    self.push_namespace()
    if tag == 'svg':
      self.push_default_namespace("http://www.w3.org/2000/svg")
    elif tag ==  'math':
      self.push_default_namespace("http://www.w3.org/1998/Math/MathML")
    else:
      self.push_default_namespace("http://www.w3.org/1999/xhtml")
    attribs = {}
    namespace = None
    # Parse get_starttag_text() for correct case of attribute names
    starttag_text = self.get_starttag_text()
    if starttag_text.endswith('/>'):
      pass
    elif starttag_text.endswith('>'):
      starttag_text = starttag_text[:-1] + '/>'
    # NOTE: XML parser doesn't handle '<' inside quotes
    #       https://www.w3.org/TR/2006/REC-xml11-20060816/
    #       [10]   	AttValue	   ::=   	'"' ([^<&"] | Reference)* '"'
		#	                               |  "'" ([^<&'] | Reference)* "'"
    starttag_text = escape_attribute_characters(starttag_text)
    parser = XmlFragmentParser(namespaceHTMLElements=False)
    try:
      parser.Parse(starttag_text, True)
    except xml.parsers.expat.ExpatError as e:
      if 'no element found' in str(e):
        pass
      else:
        raise(e)
    starttag_element = list(parser.getFragment())[0]
    attrs = starttag_element.attrib

    for key in attrs.keys():
      name = key
      val  = attrs[key]
      if name.startswith('xmlns_'):
        name = name.replace('xmlns_', 'xmlns:')
      if name == 'xmlns':
        # Add namespace to the namespace map
        namespace = val
        self.update_namespace(None, namespace)
      attribs[name] = html.unescape(val)

    token = {}
    if namespace is not None:
      tag = starttag_element.tag.replace('{' + namespace + '}', '')
    else:
      tag = starttag_element.tag
    token["name"] = tag
    token["data"] = attribs
    if namespace is not None:
      token["namespace"] = namespace
    element = self.tree.insertElementNormal(token)

  def handle_endtag(self, tag):
    self.pop_namespace()
    self.pop_default_namespace()
    self.tree.openElements.pop()

  def handle_data(self, data):
    # svgFound = self.elementInScope('http://www.w3.org/2000/svg','svg')

    # if svgFound == True:
    #   self.tree.insertText(html.escape(data, quote=False))
    # else:
    self.tree.insertText(escape_html(data))

  def handle_comment(self, data):
    self.tree.insertComment({"data": data})

  def handle_entityref(self, name):
    self.handle_data('&' + name + ';')

  def handle_charref(self, name):
    self.handle_data('&#' + name + ';')

  def handle_decl(self, data):
    self.handle_data('<!' + data + '>')

  def handle_pi(self, data):
    parser = XmlFragmentParser(namespaceHTMLElements=False)
    try:
      parser.Parse('<?' + data + '>', True)
    except xml.parsers.expat.ExpatError as e:
      if 'no element found' in str(e):
        pass
      else:
        raise(e)
    element = list(parser.getFragment())[0]

    attribs = OrderedDict()
    for key in element.attrib.keys():
      if key == "standalone":
        if element.attrib[key] == "-1":
          pass
        elif element.attrib[key] == "0":
          attribs[key] = "no"
        elif element.attrib[key] == "1":
          attribs[key] = "yes"
      else:
        attribs[key] = element.attrib[key]
    token = {}
    token["name"] = element.tag
    token["data"] = attribs
    token["namespace"] = "http://www.w3.org/2000/xmlns"
    element = self.tree.insertElementNormal(token)
    self.tree.openElements.pop()

  def unknown_decl(self, data):
    self.handle_data('<![' + data + ']>')

