import os
import re
import html5lib
import xml

import html
from html.parser import HTMLParser
from xml.etree import ElementTree

from html5lib.treebuilders import getTreeBuilder

import xml.parsers.expat

from collections import OrderedDict

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

class XmlFragmentParser:
  def __init__(self, namespaceHTMLElements=True):
    tree = getTreeBuilder("etree")
    self.tree = tree(namespaceHTMLElements)
    self.tree.insertRoot({"name": "DOCUMENT_FRAGMENT", "data": {}})
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
    self.default_namespace_ = ["http://www.w3.org/2000/xmlns/"]

    self.parser_ = xml.parsers.expat.ParserCreate()
    self.parser_.XmlDeclHandler = self.XmlDeclHandler
    self.parser_.StartDoctypeDeclHandler = self.StartDoctypeDeclHandler
    self.parser_.EndDoctypeDeclHandler = self.EndDoctypeDeclHandler
    self.parser_.ElementDeclHandler = self.ElementDeclHandler
    self.parser_.AttlistDeclHandler = self.AttlistDeclHandler
    self.parser_.StartElementHandler = self.StartElementHandler
    self.parser_.EndElementHandler = self.EndElementHandler
    self.parser_.ProcessingInstructionHandler = self.ProcessingInstructionHandler
    self.parser_.CharacterDataHandler = self.CharacterDataHandler
    self.parser_.EntityDeclHandler = self.EntityDeclHandler
    self.parser_.NotationDeclHandler = self.NotationDeclHandler
    self.parser_.StartNamespaceDeclHandler = self.StartNamespaceDeclHandler
    self.parser_.EndNamespaceDeclHandler = self.EndNamespaceDeclHandler
    self.parser_.CommentHandler = self.CommentHandler
    self.parser_.StartCdataSectionHandler = self.StartCdataSectionHandler
    self.parser_.EndCdataSectionHandler = self.EndCdataSectionHandler
    self.parser_.DefaultHandler = self.DefaultHandler
    self.parser_.DefaultHandlerExpand = self.DefaultHandlerExpand
    self.parser_.NotStandaloneHandler = self.NotStandaloneHandler
    self.parser_.ExternalEntityRefHandler = self.ExternalEntityRefHandler

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
      return self.namespace_map_.pop()
    return self.namespace_map_[-1]

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

  # NOTE: Catch xml.parsers.expat.ExpatError 'no element found' exception
  # when calling parse for XML fragments that are not elements.
  def Parse(self, data, isfinal=False):
    return self.parser_.Parse(data, isfinal)

  def XmlDeclHandler(self, version, encoding, standalone):
    name = "XML_DECL"
    attributes = OrderedDict()
    if version is not None:
      attributes["version"] = version
    if encoding is not None:
      attributes["encoding"] = encoding
    if standalone is not None:
      attributes["standalone"] = str(standalone)
    self.StartElementHandler(name, attributes)
    self.EndElementHandler(name)

  def StartDoctypeDeclHandler(self, doctypeName, systemId, publicId, has_internal_subset):
    name = "DOCTYPE_DECL"
    attributes = OrderedDict()
    if doctypeName is not None:
      attributes["name"] = doctypeName
    if publicId is not None:
      attributes["publicId"] = publicId
    if systemId is not None:
      attributes["systemId"] = systemId
    if has_internal_subset is not None:
      attributes["has_internal_subset"] = str(has_internal_subset)
    self.StartElementHandler(name, attributes)

  def EndDoctypeDeclHandler(self):
    name = "DOCTYPE_DECL"
    self.EndElementHandler(name)

  def ElementDeclHandler(self, name, model):
    name = "ELEMENT_DECL"
    attributes = OrderedDict()
    if name is not None:
      attributes["name"] = name
    if model is not None:
      attributes["model"] = model
    self.StartElementHandler(name, attributes)
    self.EndElementHandler(name)

  def AttlistDeclHandler(self, elname, attname, type_, default, required):
    name = "ATTLIST_DECL"
    attributes = OrderedDict()
    if elname is not None:
      attributes["elname"] = elname
    if attname is not None:
      attributes["attname"] = attname
    if type_ is not None:
      attributes["type"] = type_
    if default is not None:
      attributes["default"] = default
    if required is not None:
      attributes["required"] = str(required)
    self.StartElementHandler(name, attributes)
    self.EndElementHandler(name)

  def StartElementHandler(self, name, attributes):
    self.push_namespace()
    if name == 'svg':
      self.push_default_namespace("http://www.w3.org/2000/svg")
    elif name ==  'math':
      self.push_default_namespace("http://www.w3.org/1998/Math/MathML")
    elif name == 'html':
      self.push_default_namespace("http://www.w3.org/1999/xhtml")
    else:
      self.push_default_namespace("http://www.w3.org/2000/xmlns/")

    attribs = {}
    namespace = None

    for key in attributes.keys():
      attr_name = key
      attr_val  = attributes[key]
      if attr_name.startswith('xmlns_'):
        attr_name = attr_name.replace('xmlns_', 'xmlns:')
      if attr_name == 'xmlns':
        # Add namespace to the namespace map
        namespace = attr_val
        self.update_namespace(None, namespace)
      if attr_name.find(':') != -1:
        ns_prefix, attrib_name = attr_name.split(':')
        ns_uri = self.get_namespace_uri(ns_prefix)
        if ns_uri is not None:
          if ns_uri != self.default_namespace():
            attr_name = '{' + ns_uri + '}' + attrib_name
          else:
            attr_name = attrib_name

      attribs[attr_name] = attr_val

    token = {}
    token["name"] = name
    token["data"] = attribs
    if namespace is not None:
      token["namespace"] = namespace
    element = self.tree.insertElementNormal(token)

  def EndElementHandler(self, name):
    self.pop_namespace()
    self.pop_default_namespace()
    self.tree.openElements.pop()

  def ProcessingInstructionHandler(self, target, data):
    name = "PROCESSING_INSTRUCTION"
    attributes = OrderedDict()
    if target is not None:
      attributes["target"] = target
    if data is not None:
      attributes["data"] = data
    self.StartElementHandler(name, attributes)
    self.EndElementHandler(name)

  def CharacterDataHandler(self, data):
    self.tree.insertText(data)

  def EntityDeclHandler(self, entityName, is_parameter_entity, value, base, systemId, publicId, notationName):
    name = "ENTITY_DECL"
    attributes = OrderedDict()
    if entityName is not None:
      attributes["entityName"] = entityName
    if is_parameter_entity is not None:
      attributes["is_parameter_entity"] = str(is_parameter_entity)
    if value is not None:
      attributes["value"] = value
    if base is not None:
      attributes["base"] = base
    if systemId is not None:
      attributes["systemId"] = systemId
    if publicId is not None:
      attributes["publicId"] = publicId
    if notationName is not None:
      attributes["notationName"] = notationName
    self.StartElementHandler(name, attributes)
    self.EndElementHandler(name)

  def NotationDeclHandler(self, notationName, base, systemId, publicId):
    name = "NOTATION_DECL"
    attributes = OrderedDict()
    if notationName is not None:
      attributes["notationName"] = notationName
    if base is not None:
      attributes["base"] = base
    if systemId is not None:
      attributes["systemId"] = systemId
    if publicId is not None:
      attributes["publicId"] = publicId
    self.StartElementHandler(name, attributes)
    self.EndElementHandler(name)

  def StartNamespaceDeclHandler(self, prefix, uri):
    name = "NAMESPACE_DECL"
    attributes = OrderedDict()
    if prefix is not None:
      attributes["prefix"] = prefix
    if uri is not None:
      attributes["uri"] = uri
    self.StartElementHandler(name, attributes)
    self.EndElementHandler(name)

  def EndNamespaceDeclHandler(self, prefix):
    name = "NAMESPACE_DECL"
    self.EndElementHandler(name)

  def CommentHandler(self, data):
    self.tree.insertComment({"data": data})

  def StartCdataSectionHandler(self):
    pass

  def EndCdataSectionHandler(self):
    pass

  def DefaultHandler(self, data):
    self.tree.insertText(data)

  # This is the same as the DefaultHandler(), but doesn’t inhibit expansion of internal entities.
  # The entity reference will not be passed to the default handler.
  def DefaultHandlerExpand(self, data):
    self.tree.insertText(data)

  # Called if the XML document hasn’t been declared as being a standalone document.
  # This happens when there is an external subset or a reference to a parameter entity, 
  # but the XML declaration does not set standalone to yes in an XML declaration. 
  # If this handler returns 0, then the parser will raise an XML_ERROR_NOT_STANDALONE error.
  # If this handler is not set, no exception is raised by the parser for this condition.
  def NotStandaloneHandler(self):
    return 1

  # Called for references to external entities. base is the current base, as set by a previous call to SetBase().
  # The public and system identifiers, systemId and publicId, are strings if given; 
  # if the public identifier is not given, publicId will be None. 
  # The context value is opaque and should only be used as described below.
  #
  # For external entities to be parsed, this handler must be implemented. 
  # It is responsible for creating the sub-parser using ExternalEntityParserCreate(context), 
  # initializing it with the appropriate callbacks, and parsing the entity. 
  # This handler should return an integer; if it returns 0, 
  # the parser will raise an XML_ERROR_EXTERNAL_ENTITY_HANDLING error, otherwise parsing will continue.
  #
  # If this handler is not provided, external entities are reported by the DefaultHandler callback, if provided.
  def ExternalEntityRefHandler(self, context, base, systemId, publicId):
    return 0
