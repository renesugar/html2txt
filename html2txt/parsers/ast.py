import os
import sys

from . import visitor as v

from collections import OrderedDict, namedtuple
from io import StringIO
from xml.sax.saxutils import escape, quoteattr
import html

import urllib
from urllib.parse import urlparse
from urllib.parse import unquote
from urllib.parse import quote

import re

from .common import escape_url, escape_html

# TODO: (partial) In SVG and MathML, do not do any markdown formatting in nested tags.

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

class Node:
  def __init__(self):
    self.name_ = "Node"
    self.namespace_ = None
    self.namespace_map_ = {}
    self.attributes_ = OrderedDict()
    self.text_ = None
    self.tail_ = None
    self.parent_ = None
    self.children_ = []

  @property
  def tag(self):
    if self.namespace_ is None:
      return self.name_
    return "{" + self.namespace_ + "}" + self.name_

  @property
  def name(self):
    return self.name_

  @name.setter
  def name(self, name):
    self.name_ = name

  @property
  def namespace(self):
    return self.namespace_

  @namespace.setter
  def namespace(self, namespace):
    self.namespace_ = namespace

  @property
  def namespace_map(self):
    return self.namespace_map_

  @namespace_map.setter
  def namespace_map(self, namespace_map):
    self.namespace_map_ = namespace_map

  @property
  def parent(self):
    return self.parent_

  @parent.setter
  def parent(self, parent):
    self.parent_ = parent

  @property
  def children(self):
    return self.children_

  @children.setter
  def children(self, children):
    self.children_ = children

  def add_child(self, child):
    child.parent = self
    self.children_.append(child)

  @property
  def attributes(self):
    return self.attributes_

  def attribute(self, name):
    if name == "text":
      return self.text_
    if name in self.attributes_:
      return self.attributes_[name]
    return None

  def set_attribute(self, name, value):
    self.attributes_[name] = value

  @property
  def text(self):
    return self.text_

  @text.setter
  def text(self, text):
    self.text_ = text

  @property
  def tail(self):
    return self.tail_

  @tail.setter
  def tail(self, tail):
    self.tail_ = tail

  def accept(self, visitor):
    return visitor.visit(self)

# References:
# https://talk.commonmark.org/t/abbreviations-and-acronyms/890
# https://www.markdownguide.org/tools/joplin/
# https://support.squarespace.com/hc/en-us/articles/206543587
# https://github.github.com/gfm/#fenced-code-blocks
# https://github.github.com/gfm/
# https://dillinger.io/

# Notes:
# HTML tags in markdown can contain attributes.
# Joplin requires a blank line before a table to format it as a table.

# https://nedbatchelder.com/code/cog/
# cog -r ast.py
'''[[[cog
import cog

tags = [
  # Namespace                                Tag                                Open Tag              Pre-Close Tag  Close Tag      Node Text     Post Tag     Indent        Attributes    Actions
  # ---------                                ---                                --------              -------------  ---------      ---------     --------     ------        ----------    -------
  ("http://www.w3.org/1999/xhtml"          , "comment"                ,         "open_tag, close_tag = self.format_comment_tag(node.text, node.tail)",          "",            "~ignore~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "html"                   ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "base"                   ,         "open_tag, close_tag = self.format_base_tag(attr_href)",          "",            "~ignore~",            "",           "",           "",           "href",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "head"                   ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "link"                   ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "meta"                   ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "style"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "title"                  ,         "open_tag, close_tag = self.format_title_tag(node.text, node.tail)",          "",            "~ignore~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "body"                   ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "address"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "article"                ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "aside"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "footer"                 ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "header"                 ,         "",          "",            "\n\n",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "h1"                     ,         "# ",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "h2"                     ,         "## ",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "h3"                     ,         "### ",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "h4"                     ,         "#### ",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "h5"                     ,         "##### ",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "h6"                     ,         "###### ",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "hgroup"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "main"                   ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "nav"                    ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "section"                ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "blockquote"             ,         "open_tag, close_tag = self.format_blockquote_tag(node.text, node.tail)",          "node_preclose = self.preclose_blockquote_tag()",            "~ignore~",            "node_text, node_tail = self.format_blockquote_text(node.text, node.tail)",           "self.post_blockquote_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "dd"                     ,         "open_tag, close_tag = self.format_dd_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_dd_text(node.text, node.tail)",           "self.post_dd_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "div"                    ,         "open_tag, close_tag = self.format_div_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_div_text(node.text, node.tail)",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "dl"                     ,         "open_tag, close_tag = self.format_dl_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_dl_text(node.text, node.tail)",           "self.post_dl_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "dt"                     ,         "open_tag, close_tag = self.format_dt_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_dt_text(node.text, node.tail)",           "self.post_dt_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "figcaption"             ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "figure"                 ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "hr"                     ,         "\n---\n",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "li"                     ,         "open_tag, close_tag = self.format_li_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_li_text(node.text, node.tail)",           "self.post_li_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "main"                   ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "ol"                     ,         "open_tag, close_tag = self.format_ol_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_ol_text(node.text, node.tail)",           "self.post_ol_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "p"                      ,         "open_tag, close_tag = self.format_p_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_p_text(node.text, node.tail)",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "pre"                    ,         "open_tag, close_tag = self.format_pre_tag(attr_language, attr_class, node.text, node.tail)",          "",            "~ignore~",            "",           "self.close_pre_tag()",           "",           "language|class",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "ul"                     ,         "open_tag, close_tag = self.format_ul_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_ul_text(node.text, node.tail)",           "self.post_ul_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "a"                      ,         "open_tag, close_tag =self.format_link(attr_text, attr_href, attr_title)",          "",            "~ignore~",            "node_text, node_tail = self.format_link_text(node.text, node.tail)",           "",           "",           "text|href|title",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "abbr"                   ,         "open_tag, close_tag = self.format_abbr_tag(attr_title)",          "",            "~ignore~",            "node_text, node_pre_tag = self.format_abbr_text(attr_title, node.text)",           "",           "",           "title",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "b"                      ,         "**",          "",            "**",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "bdi"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "bdo"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "br"                     ,         "open_tag, close_tag = self.format_br_tag(node.text, node.tail)",          "",            "~ignore~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "cite"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "code"                   ,         "open_tag, close_tag = self.format_code_tag(attr_lang, attr_class, node.text)",          "",            "~ignore~",            "",           "self.close_code_tag()",           "",           "lang|class",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "data"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "dfn"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "em"                     ,         "*",          "",            "*",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "i"                      ,         "*",          "",            "*",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "kbd"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "mark"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "q"                      ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "rb"                     ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "rp"                     ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "rt"                     ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "rtc"                    ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "ruby"                   ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "s"                      ,         "~~",          "",            "~~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "samp"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "small"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "span"                   ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "strong"                 ,         "**",          "",            "**",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "sub"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "sup"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "time"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "u"                      ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "var"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "wbr"                    ,         "<wbr>",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "area"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "audio"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "img"                    ,         "open_tag, close_tag = self.format_img_link(attr_src, attr_alt, attr_title)",          "",            "~ignore~",            "",           "",           "",           "src|alt|title",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "map"                    ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "track"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "video"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "embed"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "iframe"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "object"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "param"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "picture"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "source"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "canvas"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "noscript"               ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "script"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "del"                    ,         "~~",          "",            "~~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "ins"                    ,         "++",          "",            "++",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "caption"                ,         "~default~",          "",            "</caption>\n",            "node_text, node_tail = self.format_caption_text(node.text, node.tail)",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "col"                    ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "colgroup"               ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "table"                  ,         "open_tag, close_tag = self.format_table_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_table_text(node.text, node.tail)",           "self.post_table_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "tbody"                  ,         "",          "",            "",            "node_text, node_tail = self.format_tbody_text(node.text, node.tail)",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "td"                     ,         "",          "",            "|",            "node_text, node_tail = self.format_td_text(attr_style, node.text, node.tail)",           "",           "",           "style",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "tfoot"                  ,         "",          "",            "",            "node_text, node_tail = self.format_tfoot_text(node.text, node.tail)",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "th"                     ,         "open_tag, close_tag = self.format_th_tag(node.text, node.tail)",          "node_preclose = self.preclose_th_tag(attr_style, attr_align, node.text, node.tail)",            "~ignore~",            "node_text, node_tail = self.format_th_text(node.text, node.tail)",           "",           "",           "style|align",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "thead"                  ,         "open_tag, close_tag = self.format_thead_tag(node.text, node.tail)",          "node_preclose = self.preclose_thead_tag()",            "~ignore~",            "node_text, node_tail = self.format_thead_text(node.text, node.tail)",           "self.post_thead_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "tr"                     ,         "open_tag, close_tag = self.format_tr_tag(node.text, node.tail)",          "",            "~ignore~",            "node_text, node_tail = self.format_tr_text(node.text, node.tail)",           "node_pre_tail = self.post_tr_tag(node)",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "button"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "datalist"               ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "fieldset"               ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "form"                   ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "input"                  ,         "open_tag, close_tag = self.format_input_tag(attr_type, attr_checked, node.text, node.tail)",          "",            "~ignore~",            "",           "",           "",           "type|checked",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "label"                  ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "legend"                 ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "meter"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "optgroup"               ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "option"                 ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "output"                 ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "progress"               ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "select"                 ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "textarea"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "details"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "dialog"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "menu"                   ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "summary"                ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "slot"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "template"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "acronym"                ,         "open_tag, close_tag = self.format_abbr_tag(attr_title)",          "",            "~ignore~",            "node_text, node_pre_tag = self.format_abbr_text(attr_title, node.text)",           "",           "",           "title",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "applet"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "basefont"               ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "bgsound"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "big"                    ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "blink"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "center"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "command"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "content"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "dir"                    ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "element"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "font"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "frame"                  ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "frameset"               ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "image"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "isindex"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "keygen"                 ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "listing"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "marquee"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "menuitem"               ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "multicol"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "nextid"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "nobr"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "noembed"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "noframes"               ,         "",          "",            "",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "plaintext"              ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "shadow"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "spacer"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "strike"                 ,         "~~",          "",            "~~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "tt"                     ,         "",          "",            "",            "",           "",           "",           "",           "ignore"),
  ("http://www.w3.org/1999/xhtml"          , "xmp"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1999/xhtml"          , "svg"                    ,         "open_tag, close_tag = self.format_svg_tag(node.text, node.tail)",          "",            "~ignore~",            "",           "self.post_svg_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "a"                      ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "animate"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "animateMotion"          ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "animateTransform"       ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "circle"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "clipPath"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "color-profile"          ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "defs"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "desc"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "discard"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "ellipse"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feBlend"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feColorMatrix"          ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feComponentTransfer"    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feComposite"            ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feConvolveMatrix"       ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feDiffuseLighting"      ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feDisplacementMap"      ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feDistantLight"         ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feDropShadow"           ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feFlood"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feFuncA"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feFuncB"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feFuncG"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feFuncR"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feGaussianBlur"         ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feImage"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feMerge"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feMergeNode"            ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feMorphology"           ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feOffset"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "fePointLight"           ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feSpecularLighting"     ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feSpotLight"            ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feTile"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "feTurbulence"           ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "filter"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "foreignObject"          ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "g"                      ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "hatch"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "hatchpath"              ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "image"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "line"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "linearGradient"         ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "marker"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "mask"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "mesh"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "meshgradient"           ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "meshpatch"              ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "meshrow"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "metadata"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "mpath"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "path"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "pattern"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "polygon"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "polyline"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "radialGradient"         ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "rect"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "script"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "set"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "solidcolor"             ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "stop"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "style"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "svg"                    ,         "open_tag, close_tag = self.format_svg_tag(node.text, node.tail)",          "",            "~ignore~",            "",           "self.post_svg_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "switch"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "symbol"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "text"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "textPath"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "title"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "tspan"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "unknown"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "use"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/svg"            , "view"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "math"                   ,         "open_tag, close_tag = self.format_math_tag(node.text, node.tail)",          "",            "~ignore~",            "",           "self.post_math_tag()",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "maction"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "maligngroup"            ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "malignmark"             ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "menclose"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "merror"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mfenced"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mfrac"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mglyph"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mi"                     ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mlabeledtr"             ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mlongdiv"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mmultiscripts"          ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mn"                     ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mo"                     ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mover"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mpadded"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mphantom"               ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mroot"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mrow"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "ms"                     ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mscarries"              ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mscarry"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "msgroup"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "msline"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mspace"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "msqrt"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "msrow"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mstack"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mstyle"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "msub"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "msup"                   ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "msubsup"                ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mtable"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mtd"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mtext"                  ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "mtr"                    ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "munder"                 ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "munderover"             ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "semantics"              ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "annotation"             ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/1998/Math/MathML"    , "annotation-xml"         ,         "~default~",          "",            "~default~",            "",           "",           "",           "",           "contents"),
  ("http://www.w3.org/2000/xmlns"          , "XML_DECL"               ,         "open_tag, close_tag = self.format_XML_DECL_tag(attr_version, attr_encoding, attr_standalone, node.text, node.tail)",              "",            "~ignore~",                   "",           "",           "",           "version|encoding|standalone",           "contents"),
]

upperFirst = lambda s: s[:1].upper() + s[1:] if s else ''
for namespace, tag, open_tag, preclose_tag, close_tag, node_text, post_tag, indent_char, attributes, actions in tags:
  node_ns   = upperFirst(namespace.split('/')[-1])
  node_name = upperFirst(tag.replace('-', ''))
  cog.outl("""# %s{%s}
class %s%sNode(Node):
  def __init__(self):
    super(%s%sNode, self).__init__()
    self.name_ = "%s"
    self.namespace_ = "%s"
""" % (namespace, tag, node_ns, node_name, node_ns, node_name, tag, namespace))
]]]'''
# http://www.w3.org/1999/xhtml{comment}
class XhtmlCommentNode(Node):
  def __init__(self):
    super(XhtmlCommentNode, self).__init__()
    self.name_ = "comment"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{html}
class XhtmlHtmlNode(Node):
  def __init__(self):
    super(XhtmlHtmlNode, self).__init__()
    self.name_ = "html"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{base}
class XhtmlBaseNode(Node):
  def __init__(self):
    super(XhtmlBaseNode, self).__init__()
    self.name_ = "base"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{head}
class XhtmlHeadNode(Node):
  def __init__(self):
    super(XhtmlHeadNode, self).__init__()
    self.name_ = "head"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{link}
class XhtmlLinkNode(Node):
  def __init__(self):
    super(XhtmlLinkNode, self).__init__()
    self.name_ = "link"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{meta}
class XhtmlMetaNode(Node):
  def __init__(self):
    super(XhtmlMetaNode, self).__init__()
    self.name_ = "meta"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{style}
class XhtmlStyleNode(Node):
  def __init__(self):
    super(XhtmlStyleNode, self).__init__()
    self.name_ = "style"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{title}
class XhtmlTitleNode(Node):
  def __init__(self):
    super(XhtmlTitleNode, self).__init__()
    self.name_ = "title"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{body}
class XhtmlBodyNode(Node):
  def __init__(self):
    super(XhtmlBodyNode, self).__init__()
    self.name_ = "body"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{address}
class XhtmlAddressNode(Node):
  def __init__(self):
    super(XhtmlAddressNode, self).__init__()
    self.name_ = "address"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{article}
class XhtmlArticleNode(Node):
  def __init__(self):
    super(XhtmlArticleNode, self).__init__()
    self.name_ = "article"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{aside}
class XhtmlAsideNode(Node):
  def __init__(self):
    super(XhtmlAsideNode, self).__init__()
    self.name_ = "aside"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{footer}
class XhtmlFooterNode(Node):
  def __init__(self):
    super(XhtmlFooterNode, self).__init__()
    self.name_ = "footer"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{header}
class XhtmlHeaderNode(Node):
  def __init__(self):
    super(XhtmlHeaderNode, self).__init__()
    self.name_ = "header"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{h1}
class XhtmlH1Node(Node):
  def __init__(self):
    super(XhtmlH1Node, self).__init__()
    self.name_ = "h1"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{h2}
class XhtmlH2Node(Node):
  def __init__(self):
    super(XhtmlH2Node, self).__init__()
    self.name_ = "h2"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{h3}
class XhtmlH3Node(Node):
  def __init__(self):
    super(XhtmlH3Node, self).__init__()
    self.name_ = "h3"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{h4}
class XhtmlH4Node(Node):
  def __init__(self):
    super(XhtmlH4Node, self).__init__()
    self.name_ = "h4"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{h5}
class XhtmlH5Node(Node):
  def __init__(self):
    super(XhtmlH5Node, self).__init__()
    self.name_ = "h5"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{h6}
class XhtmlH6Node(Node):
  def __init__(self):
    super(XhtmlH6Node, self).__init__()
    self.name_ = "h6"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{hgroup}
class XhtmlHgroupNode(Node):
  def __init__(self):
    super(XhtmlHgroupNode, self).__init__()
    self.name_ = "hgroup"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{main}
class XhtmlMainNode(Node):
  def __init__(self):
    super(XhtmlMainNode, self).__init__()
    self.name_ = "main"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{nav}
class XhtmlNavNode(Node):
  def __init__(self):
    super(XhtmlNavNode, self).__init__()
    self.name_ = "nav"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{section}
class XhtmlSectionNode(Node):
  def __init__(self):
    super(XhtmlSectionNode, self).__init__()
    self.name_ = "section"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{blockquote}
class XhtmlBlockquoteNode(Node):
  def __init__(self):
    super(XhtmlBlockquoteNode, self).__init__()
    self.name_ = "blockquote"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{dd}
class XhtmlDdNode(Node):
  def __init__(self):
    super(XhtmlDdNode, self).__init__()
    self.name_ = "dd"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{div}
class XhtmlDivNode(Node):
  def __init__(self):
    super(XhtmlDivNode, self).__init__()
    self.name_ = "div"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{dl}
class XhtmlDlNode(Node):
  def __init__(self):
    super(XhtmlDlNode, self).__init__()
    self.name_ = "dl"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{dt}
class XhtmlDtNode(Node):
  def __init__(self):
    super(XhtmlDtNode, self).__init__()
    self.name_ = "dt"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{figcaption}
class XhtmlFigcaptionNode(Node):
  def __init__(self):
    super(XhtmlFigcaptionNode, self).__init__()
    self.name_ = "figcaption"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{figure}
class XhtmlFigureNode(Node):
  def __init__(self):
    super(XhtmlFigureNode, self).__init__()
    self.name_ = "figure"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{hr}
class XhtmlHrNode(Node):
  def __init__(self):
    super(XhtmlHrNode, self).__init__()
    self.name_ = "hr"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{li}
class XhtmlLiNode(Node):
  def __init__(self):
    super(XhtmlLiNode, self).__init__()
    self.name_ = "li"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{main}
class XhtmlMainNode(Node):
  def __init__(self):
    super(XhtmlMainNode, self).__init__()
    self.name_ = "main"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{ol}
class XhtmlOlNode(Node):
  def __init__(self):
    super(XhtmlOlNode, self).__init__()
    self.name_ = "ol"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{p}
class XhtmlPNode(Node):
  def __init__(self):
    super(XhtmlPNode, self).__init__()
    self.name_ = "p"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{pre}
class XhtmlPreNode(Node):
  def __init__(self):
    super(XhtmlPreNode, self).__init__()
    self.name_ = "pre"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{ul}
class XhtmlUlNode(Node):
  def __init__(self):
    super(XhtmlUlNode, self).__init__()
    self.name_ = "ul"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{a}
class XhtmlANode(Node):
  def __init__(self):
    super(XhtmlANode, self).__init__()
    self.name_ = "a"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{abbr}
class XhtmlAbbrNode(Node):
  def __init__(self):
    super(XhtmlAbbrNode, self).__init__()
    self.name_ = "abbr"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{b}
class XhtmlBNode(Node):
  def __init__(self):
    super(XhtmlBNode, self).__init__()
    self.name_ = "b"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{bdi}
class XhtmlBdiNode(Node):
  def __init__(self):
    super(XhtmlBdiNode, self).__init__()
    self.name_ = "bdi"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{bdo}
class XhtmlBdoNode(Node):
  def __init__(self):
    super(XhtmlBdoNode, self).__init__()
    self.name_ = "bdo"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{br}
class XhtmlBrNode(Node):
  def __init__(self):
    super(XhtmlBrNode, self).__init__()
    self.name_ = "br"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{cite}
class XhtmlCiteNode(Node):
  def __init__(self):
    super(XhtmlCiteNode, self).__init__()
    self.name_ = "cite"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{code}
class XhtmlCodeNode(Node):
  def __init__(self):
    super(XhtmlCodeNode, self).__init__()
    self.name_ = "code"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{data}
class XhtmlDataNode(Node):
  def __init__(self):
    super(XhtmlDataNode, self).__init__()
    self.name_ = "data"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{dfn}
class XhtmlDfnNode(Node):
  def __init__(self):
    super(XhtmlDfnNode, self).__init__()
    self.name_ = "dfn"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{em}
class XhtmlEmNode(Node):
  def __init__(self):
    super(XhtmlEmNode, self).__init__()
    self.name_ = "em"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{i}
class XhtmlINode(Node):
  def __init__(self):
    super(XhtmlINode, self).__init__()
    self.name_ = "i"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{kbd}
class XhtmlKbdNode(Node):
  def __init__(self):
    super(XhtmlKbdNode, self).__init__()
    self.name_ = "kbd"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{mark}
class XhtmlMarkNode(Node):
  def __init__(self):
    super(XhtmlMarkNode, self).__init__()
    self.name_ = "mark"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{q}
class XhtmlQNode(Node):
  def __init__(self):
    super(XhtmlQNode, self).__init__()
    self.name_ = "q"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{rb}
class XhtmlRbNode(Node):
  def __init__(self):
    super(XhtmlRbNode, self).__init__()
    self.name_ = "rb"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{rp}
class XhtmlRpNode(Node):
  def __init__(self):
    super(XhtmlRpNode, self).__init__()
    self.name_ = "rp"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{rt}
class XhtmlRtNode(Node):
  def __init__(self):
    super(XhtmlRtNode, self).__init__()
    self.name_ = "rt"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{rtc}
class XhtmlRtcNode(Node):
  def __init__(self):
    super(XhtmlRtcNode, self).__init__()
    self.name_ = "rtc"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{ruby}
class XhtmlRubyNode(Node):
  def __init__(self):
    super(XhtmlRubyNode, self).__init__()
    self.name_ = "ruby"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{s}
class XhtmlSNode(Node):
  def __init__(self):
    super(XhtmlSNode, self).__init__()
    self.name_ = "s"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{samp}
class XhtmlSampNode(Node):
  def __init__(self):
    super(XhtmlSampNode, self).__init__()
    self.name_ = "samp"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{small}
class XhtmlSmallNode(Node):
  def __init__(self):
    super(XhtmlSmallNode, self).__init__()
    self.name_ = "small"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{span}
class XhtmlSpanNode(Node):
  def __init__(self):
    super(XhtmlSpanNode, self).__init__()
    self.name_ = "span"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{strong}
class XhtmlStrongNode(Node):
  def __init__(self):
    super(XhtmlStrongNode, self).__init__()
    self.name_ = "strong"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{sub}
class XhtmlSubNode(Node):
  def __init__(self):
    super(XhtmlSubNode, self).__init__()
    self.name_ = "sub"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{sup}
class XhtmlSupNode(Node):
  def __init__(self):
    super(XhtmlSupNode, self).__init__()
    self.name_ = "sup"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{time}
class XhtmlTimeNode(Node):
  def __init__(self):
    super(XhtmlTimeNode, self).__init__()
    self.name_ = "time"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{u}
class XhtmlUNode(Node):
  def __init__(self):
    super(XhtmlUNode, self).__init__()
    self.name_ = "u"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{var}
class XhtmlVarNode(Node):
  def __init__(self):
    super(XhtmlVarNode, self).__init__()
    self.name_ = "var"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{wbr}
class XhtmlWbrNode(Node):
  def __init__(self):
    super(XhtmlWbrNode, self).__init__()
    self.name_ = "wbr"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{area}
class XhtmlAreaNode(Node):
  def __init__(self):
    super(XhtmlAreaNode, self).__init__()
    self.name_ = "area"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{audio}
class XhtmlAudioNode(Node):
  def __init__(self):
    super(XhtmlAudioNode, self).__init__()
    self.name_ = "audio"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{img}
class XhtmlImgNode(Node):
  def __init__(self):
    super(XhtmlImgNode, self).__init__()
    self.name_ = "img"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{map}
class XhtmlMapNode(Node):
  def __init__(self):
    super(XhtmlMapNode, self).__init__()
    self.name_ = "map"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{track}
class XhtmlTrackNode(Node):
  def __init__(self):
    super(XhtmlTrackNode, self).__init__()
    self.name_ = "track"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{video}
class XhtmlVideoNode(Node):
  def __init__(self):
    super(XhtmlVideoNode, self).__init__()
    self.name_ = "video"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{embed}
class XhtmlEmbedNode(Node):
  def __init__(self):
    super(XhtmlEmbedNode, self).__init__()
    self.name_ = "embed"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{iframe}
class XhtmlIframeNode(Node):
  def __init__(self):
    super(XhtmlIframeNode, self).__init__()
    self.name_ = "iframe"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{object}
class XhtmlObjectNode(Node):
  def __init__(self):
    super(XhtmlObjectNode, self).__init__()
    self.name_ = "object"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{param}
class XhtmlParamNode(Node):
  def __init__(self):
    super(XhtmlParamNode, self).__init__()
    self.name_ = "param"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{picture}
class XhtmlPictureNode(Node):
  def __init__(self):
    super(XhtmlPictureNode, self).__init__()
    self.name_ = "picture"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{source}
class XhtmlSourceNode(Node):
  def __init__(self):
    super(XhtmlSourceNode, self).__init__()
    self.name_ = "source"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{canvas}
class XhtmlCanvasNode(Node):
  def __init__(self):
    super(XhtmlCanvasNode, self).__init__()
    self.name_ = "canvas"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{noscript}
class XhtmlNoscriptNode(Node):
  def __init__(self):
    super(XhtmlNoscriptNode, self).__init__()
    self.name_ = "noscript"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{script}
class XhtmlScriptNode(Node):
  def __init__(self):
    super(XhtmlScriptNode, self).__init__()
    self.name_ = "script"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{del}
class XhtmlDelNode(Node):
  def __init__(self):
    super(XhtmlDelNode, self).__init__()
    self.name_ = "del"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{ins}
class XhtmlInsNode(Node):
  def __init__(self):
    super(XhtmlInsNode, self).__init__()
    self.name_ = "ins"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{caption}
class XhtmlCaptionNode(Node):
  def __init__(self):
    super(XhtmlCaptionNode, self).__init__()
    self.name_ = "caption"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{col}
class XhtmlColNode(Node):
  def __init__(self):
    super(XhtmlColNode, self).__init__()
    self.name_ = "col"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{colgroup}
class XhtmlColgroupNode(Node):
  def __init__(self):
    super(XhtmlColgroupNode, self).__init__()
    self.name_ = "colgroup"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{table}
class XhtmlTableNode(Node):
  def __init__(self):
    super(XhtmlTableNode, self).__init__()
    self.name_ = "table"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{tbody}
class XhtmlTbodyNode(Node):
  def __init__(self):
    super(XhtmlTbodyNode, self).__init__()
    self.name_ = "tbody"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{td}
class XhtmlTdNode(Node):
  def __init__(self):
    super(XhtmlTdNode, self).__init__()
    self.name_ = "td"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{tfoot}
class XhtmlTfootNode(Node):
  def __init__(self):
    super(XhtmlTfootNode, self).__init__()
    self.name_ = "tfoot"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{th}
class XhtmlThNode(Node):
  def __init__(self):
    super(XhtmlThNode, self).__init__()
    self.name_ = "th"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{thead}
class XhtmlTheadNode(Node):
  def __init__(self):
    super(XhtmlTheadNode, self).__init__()
    self.name_ = "thead"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{tr}
class XhtmlTrNode(Node):
  def __init__(self):
    super(XhtmlTrNode, self).__init__()
    self.name_ = "tr"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{button}
class XhtmlButtonNode(Node):
  def __init__(self):
    super(XhtmlButtonNode, self).__init__()
    self.name_ = "button"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{datalist}
class XhtmlDatalistNode(Node):
  def __init__(self):
    super(XhtmlDatalistNode, self).__init__()
    self.name_ = "datalist"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{fieldset}
class XhtmlFieldsetNode(Node):
  def __init__(self):
    super(XhtmlFieldsetNode, self).__init__()
    self.name_ = "fieldset"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{form}
class XhtmlFormNode(Node):
  def __init__(self):
    super(XhtmlFormNode, self).__init__()
    self.name_ = "form"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{input}
class XhtmlInputNode(Node):
  def __init__(self):
    super(XhtmlInputNode, self).__init__()
    self.name_ = "input"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{label}
class XhtmlLabelNode(Node):
  def __init__(self):
    super(XhtmlLabelNode, self).__init__()
    self.name_ = "label"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{legend}
class XhtmlLegendNode(Node):
  def __init__(self):
    super(XhtmlLegendNode, self).__init__()
    self.name_ = "legend"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{meter}
class XhtmlMeterNode(Node):
  def __init__(self):
    super(XhtmlMeterNode, self).__init__()
    self.name_ = "meter"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{optgroup}
class XhtmlOptgroupNode(Node):
  def __init__(self):
    super(XhtmlOptgroupNode, self).__init__()
    self.name_ = "optgroup"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{option}
class XhtmlOptionNode(Node):
  def __init__(self):
    super(XhtmlOptionNode, self).__init__()
    self.name_ = "option"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{output}
class XhtmlOutputNode(Node):
  def __init__(self):
    super(XhtmlOutputNode, self).__init__()
    self.name_ = "output"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{progress}
class XhtmlProgressNode(Node):
  def __init__(self):
    super(XhtmlProgressNode, self).__init__()
    self.name_ = "progress"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{select}
class XhtmlSelectNode(Node):
  def __init__(self):
    super(XhtmlSelectNode, self).__init__()
    self.name_ = "select"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{textarea}
class XhtmlTextareaNode(Node):
  def __init__(self):
    super(XhtmlTextareaNode, self).__init__()
    self.name_ = "textarea"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{details}
class XhtmlDetailsNode(Node):
  def __init__(self):
    super(XhtmlDetailsNode, self).__init__()
    self.name_ = "details"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{dialog}
class XhtmlDialogNode(Node):
  def __init__(self):
    super(XhtmlDialogNode, self).__init__()
    self.name_ = "dialog"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{menu}
class XhtmlMenuNode(Node):
  def __init__(self):
    super(XhtmlMenuNode, self).__init__()
    self.name_ = "menu"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{summary}
class XhtmlSummaryNode(Node):
  def __init__(self):
    super(XhtmlSummaryNode, self).__init__()
    self.name_ = "summary"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{slot}
class XhtmlSlotNode(Node):
  def __init__(self):
    super(XhtmlSlotNode, self).__init__()
    self.name_ = "slot"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{template}
class XhtmlTemplateNode(Node):
  def __init__(self):
    super(XhtmlTemplateNode, self).__init__()
    self.name_ = "template"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{acronym}
class XhtmlAcronymNode(Node):
  def __init__(self):
    super(XhtmlAcronymNode, self).__init__()
    self.name_ = "acronym"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{applet}
class XhtmlAppletNode(Node):
  def __init__(self):
    super(XhtmlAppletNode, self).__init__()
    self.name_ = "applet"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{basefont}
class XhtmlBasefontNode(Node):
  def __init__(self):
    super(XhtmlBasefontNode, self).__init__()
    self.name_ = "basefont"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{bgsound}
class XhtmlBgsoundNode(Node):
  def __init__(self):
    super(XhtmlBgsoundNode, self).__init__()
    self.name_ = "bgsound"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{big}
class XhtmlBigNode(Node):
  def __init__(self):
    super(XhtmlBigNode, self).__init__()
    self.name_ = "big"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{blink}
class XhtmlBlinkNode(Node):
  def __init__(self):
    super(XhtmlBlinkNode, self).__init__()
    self.name_ = "blink"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{center}
class XhtmlCenterNode(Node):
  def __init__(self):
    super(XhtmlCenterNode, self).__init__()
    self.name_ = "center"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{command}
class XhtmlCommandNode(Node):
  def __init__(self):
    super(XhtmlCommandNode, self).__init__()
    self.name_ = "command"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{content}
class XhtmlContentNode(Node):
  def __init__(self):
    super(XhtmlContentNode, self).__init__()
    self.name_ = "content"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{dir}
class XhtmlDirNode(Node):
  def __init__(self):
    super(XhtmlDirNode, self).__init__()
    self.name_ = "dir"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{element}
class XhtmlElementNode(Node):
  def __init__(self):
    super(XhtmlElementNode, self).__init__()
    self.name_ = "element"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{font}
class XhtmlFontNode(Node):
  def __init__(self):
    super(XhtmlFontNode, self).__init__()
    self.name_ = "font"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{frame}
class XhtmlFrameNode(Node):
  def __init__(self):
    super(XhtmlFrameNode, self).__init__()
    self.name_ = "frame"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{frameset}
class XhtmlFramesetNode(Node):
  def __init__(self):
    super(XhtmlFramesetNode, self).__init__()
    self.name_ = "frameset"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{image}
class XhtmlImageNode(Node):
  def __init__(self):
    super(XhtmlImageNode, self).__init__()
    self.name_ = "image"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{isindex}
class XhtmlIsindexNode(Node):
  def __init__(self):
    super(XhtmlIsindexNode, self).__init__()
    self.name_ = "isindex"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{keygen}
class XhtmlKeygenNode(Node):
  def __init__(self):
    super(XhtmlKeygenNode, self).__init__()
    self.name_ = "keygen"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{listing}
class XhtmlListingNode(Node):
  def __init__(self):
    super(XhtmlListingNode, self).__init__()
    self.name_ = "listing"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{marquee}
class XhtmlMarqueeNode(Node):
  def __init__(self):
    super(XhtmlMarqueeNode, self).__init__()
    self.name_ = "marquee"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{menuitem}
class XhtmlMenuitemNode(Node):
  def __init__(self):
    super(XhtmlMenuitemNode, self).__init__()
    self.name_ = "menuitem"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{multicol}
class XhtmlMulticolNode(Node):
  def __init__(self):
    super(XhtmlMulticolNode, self).__init__()
    self.name_ = "multicol"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{nextid}
class XhtmlNextidNode(Node):
  def __init__(self):
    super(XhtmlNextidNode, self).__init__()
    self.name_ = "nextid"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{nobr}
class XhtmlNobrNode(Node):
  def __init__(self):
    super(XhtmlNobrNode, self).__init__()
    self.name_ = "nobr"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{noembed}
class XhtmlNoembedNode(Node):
  def __init__(self):
    super(XhtmlNoembedNode, self).__init__()
    self.name_ = "noembed"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{noframes}
class XhtmlNoframesNode(Node):
  def __init__(self):
    super(XhtmlNoframesNode, self).__init__()
    self.name_ = "noframes"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{plaintext}
class XhtmlPlaintextNode(Node):
  def __init__(self):
    super(XhtmlPlaintextNode, self).__init__()
    self.name_ = "plaintext"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{shadow}
class XhtmlShadowNode(Node):
  def __init__(self):
    super(XhtmlShadowNode, self).__init__()
    self.name_ = "shadow"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{spacer}
class XhtmlSpacerNode(Node):
  def __init__(self):
    super(XhtmlSpacerNode, self).__init__()
    self.name_ = "spacer"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{strike}
class XhtmlStrikeNode(Node):
  def __init__(self):
    super(XhtmlStrikeNode, self).__init__()
    self.name_ = "strike"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{tt}
class XhtmlTtNode(Node):
  def __init__(self):
    super(XhtmlTtNode, self).__init__()
    self.name_ = "tt"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{xmp}
class XhtmlXmpNode(Node):
  def __init__(self):
    super(XhtmlXmpNode, self).__init__()
    self.name_ = "xmp"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/1999/xhtml{svg}
class XhtmlSvgNode(Node):
  def __init__(self):
    super(XhtmlSvgNode, self).__init__()
    self.name_ = "svg"
    self.namespace_ = "http://www.w3.org/1999/xhtml"

# http://www.w3.org/2000/svg{a}
class SvgANode(Node):
  def __init__(self):
    super(SvgANode, self).__init__()
    self.name_ = "a"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{animate}
class SvgAnimateNode(Node):
  def __init__(self):
    super(SvgAnimateNode, self).__init__()
    self.name_ = "animate"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{animateMotion}
class SvgAnimateMotionNode(Node):
  def __init__(self):
    super(SvgAnimateMotionNode, self).__init__()
    self.name_ = "animateMotion"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{animateTransform}
class SvgAnimateTransformNode(Node):
  def __init__(self):
    super(SvgAnimateTransformNode, self).__init__()
    self.name_ = "animateTransform"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{circle}
class SvgCircleNode(Node):
  def __init__(self):
    super(SvgCircleNode, self).__init__()
    self.name_ = "circle"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{clipPath}
class SvgClipPathNode(Node):
  def __init__(self):
    super(SvgClipPathNode, self).__init__()
    self.name_ = "clipPath"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{color-profile}
class SvgColorprofileNode(Node):
  def __init__(self):
    super(SvgColorprofileNode, self).__init__()
    self.name_ = "color-profile"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{defs}
class SvgDefsNode(Node):
  def __init__(self):
    super(SvgDefsNode, self).__init__()
    self.name_ = "defs"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{desc}
class SvgDescNode(Node):
  def __init__(self):
    super(SvgDescNode, self).__init__()
    self.name_ = "desc"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{discard}
class SvgDiscardNode(Node):
  def __init__(self):
    super(SvgDiscardNode, self).__init__()
    self.name_ = "discard"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{ellipse}
class SvgEllipseNode(Node):
  def __init__(self):
    super(SvgEllipseNode, self).__init__()
    self.name_ = "ellipse"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feBlend}
class SvgFeBlendNode(Node):
  def __init__(self):
    super(SvgFeBlendNode, self).__init__()
    self.name_ = "feBlend"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feColorMatrix}
class SvgFeColorMatrixNode(Node):
  def __init__(self):
    super(SvgFeColorMatrixNode, self).__init__()
    self.name_ = "feColorMatrix"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feComponentTransfer}
class SvgFeComponentTransferNode(Node):
  def __init__(self):
    super(SvgFeComponentTransferNode, self).__init__()
    self.name_ = "feComponentTransfer"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feComposite}
class SvgFeCompositeNode(Node):
  def __init__(self):
    super(SvgFeCompositeNode, self).__init__()
    self.name_ = "feComposite"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feConvolveMatrix}
class SvgFeConvolveMatrixNode(Node):
  def __init__(self):
    super(SvgFeConvolveMatrixNode, self).__init__()
    self.name_ = "feConvolveMatrix"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feDiffuseLighting}
class SvgFeDiffuseLightingNode(Node):
  def __init__(self):
    super(SvgFeDiffuseLightingNode, self).__init__()
    self.name_ = "feDiffuseLighting"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feDisplacementMap}
class SvgFeDisplacementMapNode(Node):
  def __init__(self):
    super(SvgFeDisplacementMapNode, self).__init__()
    self.name_ = "feDisplacementMap"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feDistantLight}
class SvgFeDistantLightNode(Node):
  def __init__(self):
    super(SvgFeDistantLightNode, self).__init__()
    self.name_ = "feDistantLight"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feDropShadow}
class SvgFeDropShadowNode(Node):
  def __init__(self):
    super(SvgFeDropShadowNode, self).__init__()
    self.name_ = "feDropShadow"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feFlood}
class SvgFeFloodNode(Node):
  def __init__(self):
    super(SvgFeFloodNode, self).__init__()
    self.name_ = "feFlood"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feFuncA}
class SvgFeFuncANode(Node):
  def __init__(self):
    super(SvgFeFuncANode, self).__init__()
    self.name_ = "feFuncA"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feFuncB}
class SvgFeFuncBNode(Node):
  def __init__(self):
    super(SvgFeFuncBNode, self).__init__()
    self.name_ = "feFuncB"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feFuncG}
class SvgFeFuncGNode(Node):
  def __init__(self):
    super(SvgFeFuncGNode, self).__init__()
    self.name_ = "feFuncG"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feFuncR}
class SvgFeFuncRNode(Node):
  def __init__(self):
    super(SvgFeFuncRNode, self).__init__()
    self.name_ = "feFuncR"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feGaussianBlur}
class SvgFeGaussianBlurNode(Node):
  def __init__(self):
    super(SvgFeGaussianBlurNode, self).__init__()
    self.name_ = "feGaussianBlur"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feImage}
class SvgFeImageNode(Node):
  def __init__(self):
    super(SvgFeImageNode, self).__init__()
    self.name_ = "feImage"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feMerge}
class SvgFeMergeNode(Node):
  def __init__(self):
    super(SvgFeMergeNode, self).__init__()
    self.name_ = "feMerge"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feMergeNode}
class SvgFeMergeNodeNode(Node):
  def __init__(self):
    super(SvgFeMergeNodeNode, self).__init__()
    self.name_ = "feMergeNode"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feMorphology}
class SvgFeMorphologyNode(Node):
  def __init__(self):
    super(SvgFeMorphologyNode, self).__init__()
    self.name_ = "feMorphology"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feOffset}
class SvgFeOffsetNode(Node):
  def __init__(self):
    super(SvgFeOffsetNode, self).__init__()
    self.name_ = "feOffset"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{fePointLight}
class SvgFePointLightNode(Node):
  def __init__(self):
    super(SvgFePointLightNode, self).__init__()
    self.name_ = "fePointLight"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feSpecularLighting}
class SvgFeSpecularLightingNode(Node):
  def __init__(self):
    super(SvgFeSpecularLightingNode, self).__init__()
    self.name_ = "feSpecularLighting"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feSpotLight}
class SvgFeSpotLightNode(Node):
  def __init__(self):
    super(SvgFeSpotLightNode, self).__init__()
    self.name_ = "feSpotLight"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feTile}
class SvgFeTileNode(Node):
  def __init__(self):
    super(SvgFeTileNode, self).__init__()
    self.name_ = "feTile"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{feTurbulence}
class SvgFeTurbulenceNode(Node):
  def __init__(self):
    super(SvgFeTurbulenceNode, self).__init__()
    self.name_ = "feTurbulence"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{filter}
class SvgFilterNode(Node):
  def __init__(self):
    super(SvgFilterNode, self).__init__()
    self.name_ = "filter"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{foreignObject}
class SvgForeignObjectNode(Node):
  def __init__(self):
    super(SvgForeignObjectNode, self).__init__()
    self.name_ = "foreignObject"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{g}
class SvgGNode(Node):
  def __init__(self):
    super(SvgGNode, self).__init__()
    self.name_ = "g"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{hatch}
class SvgHatchNode(Node):
  def __init__(self):
    super(SvgHatchNode, self).__init__()
    self.name_ = "hatch"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{hatchpath}
class SvgHatchpathNode(Node):
  def __init__(self):
    super(SvgHatchpathNode, self).__init__()
    self.name_ = "hatchpath"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{image}
class SvgImageNode(Node):
  def __init__(self):
    super(SvgImageNode, self).__init__()
    self.name_ = "image"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{line}
class SvgLineNode(Node):
  def __init__(self):
    super(SvgLineNode, self).__init__()
    self.name_ = "line"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{linearGradient}
class SvgLinearGradientNode(Node):
  def __init__(self):
    super(SvgLinearGradientNode, self).__init__()
    self.name_ = "linearGradient"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{marker}
class SvgMarkerNode(Node):
  def __init__(self):
    super(SvgMarkerNode, self).__init__()
    self.name_ = "marker"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{mask}
class SvgMaskNode(Node):
  def __init__(self):
    super(SvgMaskNode, self).__init__()
    self.name_ = "mask"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{mesh}
class SvgMeshNode(Node):
  def __init__(self):
    super(SvgMeshNode, self).__init__()
    self.name_ = "mesh"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{meshgradient}
class SvgMeshgradientNode(Node):
  def __init__(self):
    super(SvgMeshgradientNode, self).__init__()
    self.name_ = "meshgradient"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{meshpatch}
class SvgMeshpatchNode(Node):
  def __init__(self):
    super(SvgMeshpatchNode, self).__init__()
    self.name_ = "meshpatch"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{meshrow}
class SvgMeshrowNode(Node):
  def __init__(self):
    super(SvgMeshrowNode, self).__init__()
    self.name_ = "meshrow"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{metadata}
class SvgMetadataNode(Node):
  def __init__(self):
    super(SvgMetadataNode, self).__init__()
    self.name_ = "metadata"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{mpath}
class SvgMpathNode(Node):
  def __init__(self):
    super(SvgMpathNode, self).__init__()
    self.name_ = "mpath"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{path}
class SvgPathNode(Node):
  def __init__(self):
    super(SvgPathNode, self).__init__()
    self.name_ = "path"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{pattern}
class SvgPatternNode(Node):
  def __init__(self):
    super(SvgPatternNode, self).__init__()
    self.name_ = "pattern"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{polygon}
class SvgPolygonNode(Node):
  def __init__(self):
    super(SvgPolygonNode, self).__init__()
    self.name_ = "polygon"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{polyline}
class SvgPolylineNode(Node):
  def __init__(self):
    super(SvgPolylineNode, self).__init__()
    self.name_ = "polyline"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{radialGradient}
class SvgRadialGradientNode(Node):
  def __init__(self):
    super(SvgRadialGradientNode, self).__init__()
    self.name_ = "radialGradient"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{rect}
class SvgRectNode(Node):
  def __init__(self):
    super(SvgRectNode, self).__init__()
    self.name_ = "rect"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{script}
class SvgScriptNode(Node):
  def __init__(self):
    super(SvgScriptNode, self).__init__()
    self.name_ = "script"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{set}
class SvgSetNode(Node):
  def __init__(self):
    super(SvgSetNode, self).__init__()
    self.name_ = "set"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{solidcolor}
class SvgSolidcolorNode(Node):
  def __init__(self):
    super(SvgSolidcolorNode, self).__init__()
    self.name_ = "solidcolor"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{stop}
class SvgStopNode(Node):
  def __init__(self):
    super(SvgStopNode, self).__init__()
    self.name_ = "stop"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{style}
class SvgStyleNode(Node):
  def __init__(self):
    super(SvgStyleNode, self).__init__()
    self.name_ = "style"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{svg}
class SvgSvgNode(Node):
  def __init__(self):
    super(SvgSvgNode, self).__init__()
    self.name_ = "svg"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{switch}
class SvgSwitchNode(Node):
  def __init__(self):
    super(SvgSwitchNode, self).__init__()
    self.name_ = "switch"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{symbol}
class SvgSymbolNode(Node):
  def __init__(self):
    super(SvgSymbolNode, self).__init__()
    self.name_ = "symbol"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{text}
class SvgTextNode(Node):
  def __init__(self):
    super(SvgTextNode, self).__init__()
    self.name_ = "text"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{textPath}
class SvgTextPathNode(Node):
  def __init__(self):
    super(SvgTextPathNode, self).__init__()
    self.name_ = "textPath"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{title}
class SvgTitleNode(Node):
  def __init__(self):
    super(SvgTitleNode, self).__init__()
    self.name_ = "title"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{tspan}
class SvgTspanNode(Node):
  def __init__(self):
    super(SvgTspanNode, self).__init__()
    self.name_ = "tspan"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{unknown}
class SvgUnknownNode(Node):
  def __init__(self):
    super(SvgUnknownNode, self).__init__()
    self.name_ = "unknown"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{use}
class SvgUseNode(Node):
  def __init__(self):
    super(SvgUseNode, self).__init__()
    self.name_ = "use"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/2000/svg{view}
class SvgViewNode(Node):
  def __init__(self):
    super(SvgViewNode, self).__init__()
    self.name_ = "view"
    self.namespace_ = "http://www.w3.org/2000/svg"

# http://www.w3.org/1998/Math/MathML{math}
class MathMLMathNode(Node):
  def __init__(self):
    super(MathMLMathNode, self).__init__()
    self.name_ = "math"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{maction}
class MathMLMactionNode(Node):
  def __init__(self):
    super(MathMLMactionNode, self).__init__()
    self.name_ = "maction"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{maligngroup}
class MathMLMaligngroupNode(Node):
  def __init__(self):
    super(MathMLMaligngroupNode, self).__init__()
    self.name_ = "maligngroup"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{malignmark}
class MathMLMalignmarkNode(Node):
  def __init__(self):
    super(MathMLMalignmarkNode, self).__init__()
    self.name_ = "malignmark"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{menclose}
class MathMLMencloseNode(Node):
  def __init__(self):
    super(MathMLMencloseNode, self).__init__()
    self.name_ = "menclose"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{merror}
class MathMLMerrorNode(Node):
  def __init__(self):
    super(MathMLMerrorNode, self).__init__()
    self.name_ = "merror"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mfenced}
class MathMLMfencedNode(Node):
  def __init__(self):
    super(MathMLMfencedNode, self).__init__()
    self.name_ = "mfenced"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mfrac}
class MathMLMfracNode(Node):
  def __init__(self):
    super(MathMLMfracNode, self).__init__()
    self.name_ = "mfrac"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mglyph}
class MathMLMglyphNode(Node):
  def __init__(self):
    super(MathMLMglyphNode, self).__init__()
    self.name_ = "mglyph"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mi}
class MathMLMiNode(Node):
  def __init__(self):
    super(MathMLMiNode, self).__init__()
    self.name_ = "mi"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mlabeledtr}
class MathMLMlabeledtrNode(Node):
  def __init__(self):
    super(MathMLMlabeledtrNode, self).__init__()
    self.name_ = "mlabeledtr"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mlongdiv}
class MathMLMlongdivNode(Node):
  def __init__(self):
    super(MathMLMlongdivNode, self).__init__()
    self.name_ = "mlongdiv"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mmultiscripts}
class MathMLMmultiscriptsNode(Node):
  def __init__(self):
    super(MathMLMmultiscriptsNode, self).__init__()
    self.name_ = "mmultiscripts"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mn}
class MathMLMnNode(Node):
  def __init__(self):
    super(MathMLMnNode, self).__init__()
    self.name_ = "mn"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mo}
class MathMLMoNode(Node):
  def __init__(self):
    super(MathMLMoNode, self).__init__()
    self.name_ = "mo"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mover}
class MathMLMoverNode(Node):
  def __init__(self):
    super(MathMLMoverNode, self).__init__()
    self.name_ = "mover"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mpadded}
class MathMLMpaddedNode(Node):
  def __init__(self):
    super(MathMLMpaddedNode, self).__init__()
    self.name_ = "mpadded"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mphantom}
class MathMLMphantomNode(Node):
  def __init__(self):
    super(MathMLMphantomNode, self).__init__()
    self.name_ = "mphantom"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mroot}
class MathMLMrootNode(Node):
  def __init__(self):
    super(MathMLMrootNode, self).__init__()
    self.name_ = "mroot"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mrow}
class MathMLMrowNode(Node):
  def __init__(self):
    super(MathMLMrowNode, self).__init__()
    self.name_ = "mrow"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{ms}
class MathMLMsNode(Node):
  def __init__(self):
    super(MathMLMsNode, self).__init__()
    self.name_ = "ms"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mscarries}
class MathMLMscarriesNode(Node):
  def __init__(self):
    super(MathMLMscarriesNode, self).__init__()
    self.name_ = "mscarries"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mscarry}
class MathMLMscarryNode(Node):
  def __init__(self):
    super(MathMLMscarryNode, self).__init__()
    self.name_ = "mscarry"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{msgroup}
class MathMLMsgroupNode(Node):
  def __init__(self):
    super(MathMLMsgroupNode, self).__init__()
    self.name_ = "msgroup"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{msline}
class MathMLMslineNode(Node):
  def __init__(self):
    super(MathMLMslineNode, self).__init__()
    self.name_ = "msline"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mspace}
class MathMLMspaceNode(Node):
  def __init__(self):
    super(MathMLMspaceNode, self).__init__()
    self.name_ = "mspace"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{msqrt}
class MathMLMsqrtNode(Node):
  def __init__(self):
    super(MathMLMsqrtNode, self).__init__()
    self.name_ = "msqrt"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{msrow}
class MathMLMsrowNode(Node):
  def __init__(self):
    super(MathMLMsrowNode, self).__init__()
    self.name_ = "msrow"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mstack}
class MathMLMstackNode(Node):
  def __init__(self):
    super(MathMLMstackNode, self).__init__()
    self.name_ = "mstack"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mstyle}
class MathMLMstyleNode(Node):
  def __init__(self):
    super(MathMLMstyleNode, self).__init__()
    self.name_ = "mstyle"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{msub}
class MathMLMsubNode(Node):
  def __init__(self):
    super(MathMLMsubNode, self).__init__()
    self.name_ = "msub"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{msup}
class MathMLMsupNode(Node):
  def __init__(self):
    super(MathMLMsupNode, self).__init__()
    self.name_ = "msup"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{msubsup}
class MathMLMsubsupNode(Node):
  def __init__(self):
    super(MathMLMsubsupNode, self).__init__()
    self.name_ = "msubsup"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mtable}
class MathMLMtableNode(Node):
  def __init__(self):
    super(MathMLMtableNode, self).__init__()
    self.name_ = "mtable"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mtd}
class MathMLMtdNode(Node):
  def __init__(self):
    super(MathMLMtdNode, self).__init__()
    self.name_ = "mtd"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mtext}
class MathMLMtextNode(Node):
  def __init__(self):
    super(MathMLMtextNode, self).__init__()
    self.name_ = "mtext"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{mtr}
class MathMLMtrNode(Node):
  def __init__(self):
    super(MathMLMtrNode, self).__init__()
    self.name_ = "mtr"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{munder}
class MathMLMunderNode(Node):
  def __init__(self):
    super(MathMLMunderNode, self).__init__()
    self.name_ = "munder"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{munderover}
class MathMLMunderoverNode(Node):
  def __init__(self):
    super(MathMLMunderoverNode, self).__init__()
    self.name_ = "munderover"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{semantics}
class MathMLSemanticsNode(Node):
  def __init__(self):
    super(MathMLSemanticsNode, self).__init__()
    self.name_ = "semantics"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{annotation}
class MathMLAnnotationNode(Node):
  def __init__(self):
    super(MathMLAnnotationNode, self).__init__()
    self.name_ = "annotation"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/1998/Math/MathML{annotation-xml}
class MathMLAnnotationxmlNode(Node):
  def __init__(self):
    super(MathMLAnnotationxmlNode, self).__init__()
    self.name_ = "annotation-xml"
    self.namespace_ = "http://www.w3.org/1998/Math/MathML"

# http://www.w3.org/2000/xmlns{XML_DECL}
class XmlnsXML_DECLNode(Node):
  def __init__(self):
    super(XmlnsXML_DECLNode, self).__init__()
    self.name_ = "XML_DECL"
    self.namespace_ = "http://www.w3.org/2000/xmlns"

#[[[end]]]

def attr_breaks(tag, attributes, indent, max_line_length):
  breaks = set()
  i = 0
  total_length = 0
  for name, value in attributes.items():
    attr_length = len(name) + len(quoteattr(value)) + 2
    indent_length = indent + len(tag) + 2 # '<tag '
    remaining_length = max_line_length - indent_length
    if i > 0:
      if (total_length + attr_length) > remaining_length:
        breaks.add(i)
    i += 1
  return breaks

def format_html_tag(tag, attributes, indent, indent_char, max_line_length, is_empty, text, tail, newline_char):
  breaks = attr_breaks(tag, attributes, indent, max_line_length)
  indent_str = indent_char * (len(tag) + 2)
  if tag == "Node":
    tag_str = ""
    open_tag_suffix = ""
    close_tag_suffix = ""
  else:
    tag_str = "<%s" % (tag,)
    if is_empty == True:
      open_tag_suffix = "/>"
      close_tag_suffix = ""
    else:
      open_tag_suffix = ">"
      close_tag_suffix = "</%s>" % (tag,)
  i = 0
  for name, value in attributes.items():
    if i in breaks:
      tag_str += newline_char
      tag_str += indent_str
    if value is None:
      tag_str += " %s" % (name,)
    else:
      tag_str += " %s=%s" % (name, quoteattr(value),)
    i += 1
  tag_str += open_tag_suffix

  return (tag_str, close_tag_suffix)

def langCanonicalize(lang):
  if lang is None:
    return ''

  lang = lang.lower()

  if lang == 'js' or lang == 'javascript':
    return 'js'

  if lang == 'md' or lang == 'mdown' or lang == 'mkdown' or lang == 'markdown':
    return 'md'

  return lang

class MarkdownVisitor:
  def __init__(self):
    self.data_ = [StringIO()]
    self.indent_ = 0
    self.indent_char_ = ' '
    self.newline_char_ = os.linesep
    self.max_line_length_ = 80
    self.blockquotes_ = 0
    self.blockquotes_newline = True # set to False if line doesn't end with a newline
    self.pre_ = 0
    self.code_ = 0
    self.pre_language = ''
    self.base_href_ = ''
    self.list_stack_ = []
    self.table_dict_ = []
    self.thead_ = 0
    self.table_ = 0
    self.svg_ = 0
    self.math_ = 0

  def InXmlScope(self):
    return self.svg_ > 0 or self.math_ > 0

  def push_data_source(self):
    self.data_.append(StringIO())

  def pop_data_source(self):
    self.data_.pop()

  def write_data(self, data=''):
    if data is None:
      return
    self.data_[-1].write(data)

  def is_header_row(self, node):
    status = True
    count = 0
    for n in node.children:
      count += 1
      if n.name != 'th':
        status = False
        break
    return (status, count)

  def list_indent(self):
    if (len(self.list_stack_) - 1) > 0:
      indent = (len(self.list_stack_) - 1) * '    '
    else:
      indent = ''
    return indent

  def format_link(self, attr_text, attr_href, attr_title):
    if attr_text is None:
      attr_text = ""

    if attr_href is None:
      return (None, None)

    if attr_href == '':
      return (None, None)

    # Check for missing URL scheme
    urlTuple = urllib.parse.urlsplit(attr_href)
    if urlTuple.scheme == '':
      attr_href = 'https://' + urlTuple.path

    # NOTE: Autolink format causes problems with markdown2, XML parser, and BeautifulSoup
    #       when the URL scheme is missing.
    #
    #       Remove support for <https://www.google.com>
    #       and change to [https://www.google.com](https://www.google.com)
    #
    # If the URL scheme is missing (e.g. <www.google.com>), the link is not converted to HTML
    # by markdown2 causing BeautifulSoup to misinterpret the markdown link as an HTML tag.
    #

    # Autolink format
    # if attr_text == "":
    #   open_tag = "<" + attr_href
    #   close_tag = ">"
    #   return (open_tag, close_tag)
    # elif unquote(attr_href) == attr_text:
    #   open_tag = "<"
    #   close_tag = ">"
    #   return (open_tag, close_tag)

    open_tag = "["
    close_tag = ""

    #
    # NOTE: Mistune markdown parser does not reverse escape inside link URL
    #

    # Format joplin: URL
    #
    # e.g. [FILE.pdf](:/a56a1e70f3b14bb085f8b8d7794c05fc)
    if attr_href.startswith('joplin:'):
      resource  = attr_href.split('/')[-2]
      file_name = attr_href.split('/')[-1]
      close_tag = f"""{file_name}](:/{resource})"""
    else:
      # Self-closing tag or text for link is missing so use URL
      if attr_text == "":
        open_tag += escape_html(attr_href)
      attr_href = escape_url(attr_href)
      if attr_title is None:
        close_tag = f"""]({attr_href})"""
      else:
        attr_title = escape_html(attr_title)
        close_tag = f"""]({attr_href} "{attr_title}")"""

    return (open_tag, close_tag)

  def format_link_text(self, text, tail):
    return (escape_html(text), tail)

  def format_img_link(self, attr_src, attr_alt, attr_title):
    if attr_alt is None:
      attr_alt = ""

    open_tag = "!["
    close_tag = ""

    #
    # NOTE: Mistune markdown parser does not reverse escape inside link URL
    #

    # Format joplin: URL
    #
    # e.g. ![IMAGE.JPG](:/7dd8b560cbc1467693f024d650870a0c)
    if attr_src.startswith('joplin:'):
      resource  = attr_src.split('/')[-2]
      file_name = attr_src.split('/')[-1]
      close_tag = f"""{file_name}](:/{resource})"""
    else:
      attr_alt = escape_html(attr_alt)
      attr_src = escape_url(attr_src)
      if attr_title is None:
        close_tag = f"""{attr_alt}]({attr_src})"""
      else:
        attr_title = escape_html(attr_title)
        close_tag = f"""{attr_alt}]({attr_src} "{attr_title}")"""
    return (open_tag, close_tag)

  def format_caption_text(self, text, tail):
    return (text, '\n')

  def format_table_tag(self, text, tail):
    self.table_ += 1
    table_dict = {}
    table_dict['columns'] = 0
    table_dict['header'] = []
    table_dict['alignment'] = []

    self.table_dict_.append(table_dict)
    open_tag = "\n"
    close_tag = "\n"
    return (open_tag, close_tag)

  def format_table_text(self, text, tail):
    return (None, tail)

  def post_table_tag(self):
    if len(self.table_dict_) > 0:
      self.table_dict_.pop()
    self.table_ -= 1

  def format_thead_tag(self, text, tail):
    self.thead_ += 1
    open_tag = ""
    close_tag =  ""
    return (open_tag, close_tag)

  def format_thead_text(self, text, tail):
    return (None, None)

  def preclose_thead_tag(self):
    header_row = ""
    alignment_row = ""
    if len(self.table_dict_) > 0:
      header_cols = []
      header_row = "|"
      align_cols = []
      alignment_row = "|"
      table_dict = self.table_dict_[-1]
      num_columns = table_dict['columns']
      alignment = table_dict['alignment']
      num_alignment = len(alignment)
      header = table_dict['header']
      num_header = len(header)

      if (num_alignment % num_columns) != 0:
        if num_columns > num_alignment:
          num_missing = num_columns - num_alignment
        else:
          num_missing = num_alignment - num_columns
        for i in range(num_missing):
          alignment.append(None)

      if (num_header % num_columns) != 0:
        if num_columns > num_header:
          num_missing = num_columns - num_header
        else:
          num_missing = num_header - num_columns
        for i in range(num_missing):
          header.append('')

      for i in range(num_columns):
        header_cols.append('')
        align_cols.append('')

      j = 0
      for i in range(num_header):
        if i % num_columns == 0:
          j = 0
        header_col = header_cols[j]
        header_val = header[i]
        if header_val is None:
          header_val = ''
        if header_col == '':
          header_col = header_val
        else:
          header_col += '<br>' + header_val
        header_cols[j] = header_col
        j += 1

      j = 0
      for i in range(num_alignment):
        if i % num_columns == 0:
          j = 0
        align_col = align_cols[j]
        align_val = alignment[i]
        if align_val is not None:
          align_col = align_val
        align_cols[j] = align_col
        j += 1

      for i in range(num_columns):
        align_col = align_cols[i]
        if align_col is None:
          align_cols[i] = '---'

      for i in range(num_columns):
        header_row += header_cols[i] + '|'
      header_row += '\n'

      for i in range(num_columns):
        alignment_row += align_cols[i] + '|'
      alignment_row += '\n'
    return header_row + alignment_row

  def post_thead_tag(self):
    self.thead_ -= 1

  def format_tbody_text(self, text, tail):
    return (None, None)

  def format_tfoot_text(self, text, tail):
    return (None, None)

  def format_tr_tag(self, text, tail):
    if len(self.table_dict_) > 0:
      table_dict = self.table_dict_[-1]
      table_dict['columns'] = 0
      self.table_dict_[-1] = table_dict
    if self.thead_ > 0:
      open_tag = ""
    else:
      open_tag = "|"
    close_tag = ""
    return (open_tag, close_tag)

  def format_tr_text(self, text, tail):
    if self.thead_ > 0:
      return (None, None)
    return (None, '\n')

  def post_tr_tag(self, node):
    header_row = None
    if self.thead_ == 0:
      is_header, num_columns = self.is_header_row(node)
      if is_header == True:
        header_row = '\n|'
        for i in range(num_columns):
          header_row += '---|'
    return header_row

  def format_th_tag(self, text, tail):
    self.push_data_source()

    open_tag = ""
    if self.thead_ > 0:
      close_tag =  ""
    else:
      close_tag = "|"
    return (open_tag, close_tag)

  def format_th_text(self, text, tail):
    if self.thead_ > 0:
      return (None, None)
    return (text, None)

  def preclose_th_tag(self, attr_style, attr_align, text, tail):
    if text is None:
      text = ''
    th_text = self.text
    self.pop_data_source()

    if self.thead_ > 0:
      if len(self.table_dict_) > 0:
        table_dict = self.table_dict_[-1]
        table_dict['columns'] = table_dict['columns'] + 1
        self.table_dict_[-1] = table_dict
      if attr_style is None:
        attr_style = ''
      if attr_align is None:
        attr_align = ''
      if attr_style.find("text-align:left") != -1 or attr_align == "left":
        align_col = ":---"
      elif attr_style.find("text-align:center") != -1 or attr_align == "center":
        align_col = ":---:"
      elif attr_style.find("text-align:right") != -1 or attr_align == "right":
        align_col = "---:"
      else:
        align_col = "---"
      if len(self.table_dict_) > 0:
        table_dict = self.table_dict_[-1]
        alignment = table_dict['alignment']
        alignment.append(align_col)
        header = table_dict['header']
        header.append(text + th_text)
        table_dict['header'] = header
        table_dict['alignment'] = alignment
        self.table_dict_[-1] = table_dict
        return None
    else:
      return th_text

  def format_td_text(self, attr_style, text, tail):
    if len(self.table_dict_) > 0:
      table_dict = self.table_dict_[-1]
      table_dict['columns'] = table_dict['columns'] + 1
      self.table_dict_[-1] = table_dict
    return (text, None)

  def format_dl_tag(self, text, tail):
    self.list_stack_.append(': ')
    open_tag = ""
    close_tag = ""
    return (open_tag, close_tag)

  def format_dl_text(self, text, tail):
    return (None, tail)

  def post_dl_tag(self):
    if len(self.list_stack_) > 0:
      self.list_stack_.pop()

  def format_dt_tag(self, text, tail):
    open_tag = ""
    close_tag = "\n"
    return (open_tag, close_tag)

  def format_dt_text(self, text, tail):
    indent = self.list_indent()
    if text is None:
      text =  ''
    prefix = ''
    return (indent + prefix + text.strip(), None)

  def post_dt_tag(self):
    pass

  def format_dd_tag(self, text, tail):
    open_tag = ""
    close_tag = "\n"
    return (open_tag, close_tag)

  def format_dd_text(self, text, tail):
    indent = self.list_indent()
    if text is None:
      text =  ''
    if len(self.list_stack_) > 0:
      prefix = self.list_stack_[-1]
    else:
      # default to definition list if syntax error
      prefix = ': '
    return (indent + prefix + text.strip(), None)

  def post_dd_tag(self):
    pass

  def format_ol_tag(self, text, tail):
    self.list_stack_.append('1. ')
    open_tag = ""
    close_tag = ""
    return (open_tag, close_tag)

  def format_ol_text(self, text, tail):
    return (None, tail)

  def post_ol_tag(self):
    if len(self.list_stack_) > 0:
      self.list_stack_.pop()

  def format_ul_tag(self, text, tail):
    self.list_stack_.append('* ')
    open_tag = ""
    close_tag = ""
    return (open_tag, close_tag)

  def format_ul_text(self, text, tail):
    return (None, tail)

  def post_ul_tag(self):
    if len(self.list_stack_) > 0:
      self.list_stack_.pop()

  def format_li_tag(self, text, tail):
    open_tag = ""
    close_tag = "\n"
    return (open_tag, close_tag)

  def format_li_text(self, text, tail):
    indent = self.list_indent()
    if text is None:
      text =  ''
    if len(self.list_stack_) > 0:
      prefix = self.list_stack_[-1]
    else:
      # default to unordered list if syntax error
      prefix = '- '
    return (indent + prefix + text, None)

  def post_li_tag(self):
    pass

  def format_input_tag(self, attr_type, attr_checked, text, tail):
    open_tag = "["
    close_tag = ""

    if attr_type == "checkbox" or attr_type == "radio":
      if attr_checked is not None:
        open_tag += "x] "
      else:
        open_tag += " ] "

    return (open_tag, close_tag)

  def format_br_tag(self, text, tail):
    # NOTE: Joplin does not display URLs when <br> is used:
    # https://github.com/laurent22/joplin/issues/3270
    # https://github.com/laurent22/joplin/issues/3274

    if tail is None:
      tail = ''
    open_tag = ""
    close_tag = ""
    if tail.startswith('\n'):
      open_tag = "\n  "
    else:
      open_tag = "\n  \n"
    return (open_tag, close_tag)

  def format_p_tag(self, text, tail):
    if self.table_ > 0:
      # newline characters break table formatting inside a table
      return ('', '')

    open_tag = ''
    close_tag = '\n'
    if text is not None:
      if text.endswith('\n'):
        close_tag = ''
    return (open_tag, close_tag)

  def format_p_text(self, text, tail):
    if text is not None:
      return (text.strip(), tail)
    return (text, tail)

  def format_div_tag(self, text, tail):
    if self.table_ > 0:
      # newline characters break table formatting inside a table
      return ('', '')

    open_tag = ''
    close_tag = '\n'
    if text is not None:
      if text.endswith('\n'):
        close_tag = ''
    return (open_tag, close_tag)

  def format_div_text(self, text, tail):
    if text is not None:
      return (text.strip(), tail)
    return (text, tail)

  def format_XML_DECL_tag(self, attr_version, attr_encoding, attr_standalone, text, tail):
    open_tag = '<?xml'
    close_tag = '?>'

    if attr_version is not None:
      open_tag += ' version="' + attr_version + '"'

    if attr_encoding is not None:
      open_tag += ' encoding="' + attr_encoding + '"'

    if attr_standalone is not None:
      open_tag += ' standalone="' + attr_standalone + '"'

    return (open_tag, close_tag)

  def format_pre_tag(self, attr_language, attr_class, text, tail):
    self.pre_ += 1

    is_codebrush = False
    if attr_language is not None:
      self.pre_language = attr_language

    # https://github.com/benfields/code-brush
    if attr_class is not None:
      class_attribs = attr_class.split(',')
      for attrib in class_attribs:
        name_value = attrib.split(':')
        if len(name_value) == 2:
          attrib_name = name_value[0]
          attrib_value = name_value[1]
          if attrib_name is not None:
            attrib_name = attrib_name.strip()
          if attrib_value is not None:
            attrib_value = attrib_value.strip()
          if attrib_name == "brush":
            is_codebrush = True
            self.pre_language = attrib_value
            break
    if is_codebrush == True:
      language = self.pre_language

      if language is None:
        language =  ''
      
      language = langCanonicalize(language)

      open_tag = f"""\n\n```{language}\n"""
      close_tag = '\n```\n\n'
      return (open_tag, close_tag)

    open_tag = "\n<pre>"
    close_tag = "</pre>\n\n"
    if text is not None:
      if text.endswith('\n'):
        close_tag = ''
    if tail is not None:
      if tail.startswith('\n'):
        pass
      else:
        close_tag += '\n'
    if self.blockquotes_ > 0:
      return (open_tag, close_tag)
    return (open_tag, close_tag)

  def close_pre_tag(self):
    self.pre_ -= 1
    self.pre_language = ''

  def format_code_tag(self, attr_lang, attr_class, text):
    self.code_ += 1

    open_tag = ''
    close_tag = ''

    if text is None:
      text = ''
    if text.find('\n') == -1:
      open_tag = '`'
      close_tag = '`'
      return (open_tag, close_tag)

    language = self.pre_language

    if language is None:
      language =  ''

    if attr_class is not None:
      if attr_class.startswith("language-"):
        language = attr_class.split('-')[1]

    if attr_lang is not None:
      language = attr_lang
    
    language = langCanonicalize(language)

    open_tag = f"""\n\n```{language}\n"""
    close_tag = '\n```\n\n'
    return (open_tag, close_tag)

  def close_code_tag(self):
    self.code_ -= 1

  def format_comment_tag(self, text, tail):
    if self.InXmlScope():
      open_tag = '<!--'
      close_tag = '-->'
      return (open_tag, close_tag)

    open_tag = '[//]: # ('
    close_tag = ')'
    return (open_tag, close_tag)

  def format_title_tag(self, text, tail):
    if self.InXmlScope():
      return (None, None)

    open_tag = '% '
    close_tag = '\n\n'
    return (open_tag, close_tag)

  def format_svg_tag(self, text, tail):
    self.svg_ += 1

    return (None, None)

  def post_svg_tag(self):
    self.svg_ -= 1

  def format_math_tag(self, text, tail):
    self.math_ += 1

    return (None, None)

  def post_math_tag(self):
    self.math_ -= 1

  def format_blockquote_tag(self, text, tail):
    self.blockquotes_ += 1
    self.push_data_source()

    open_tag = ''
    close_tag = ''
    return (open_tag, close_tag)

  def format_blockquote_text(self, text, tail):
    return (None, None)

  def preclose_blockquote_tag(self):
    blockquote_text = self.text
    self.pop_data_source()

    indent = ""
    if self.pre_ == 0 and self.code_ == 0:
      if self.blockquotes_ > 0:
        indent = self.blockquotes_ * '>'
    lines = blockquote_text.splitlines(keepends=True)
    for line in lines:
      if line.endswith('\n'):
        self.write_data(indent + line)
      else:
        self.write_data(indent + line + '\n')

  def post_blockquote_tag(self):
    self.blockquotes_ -= 1

  def format_base_tag(self, attr_href):
    if attr_href is not None:
      self.base_href_ = attr_href

    open_tag = ''
    close_tag = ''
    return (open_tag, close_tag)

  def format_abbr_tag(self, attr_title):
    open_tag = ''
    close_tag = ''
    return (open_tag, close_tag)

  def format_abbr_text(self, attr_title, text):
    if attr_title is None:
      node_text = text
      node_pre_tail = ''
    else:
      node_text = attr_title
      node_pre_tail = f"\n*[{text}]: {attr_title}\n\n"
    return (node_text, node_pre_tail)

  @property
  def indent_char(self):
    return self.indent_char_

  @indent_char.setter
  def indent_char(self, indent_char):
    self.indent_char_ = indent_char

  @property
  def newline_char(self):
    return self.newline_char_

  @newline_char.setter
  def newline_char(self, newline_char):
    self.newline_char_ = newline_char

  @property
  def max_line_length(self):
    return self.max_line_length_

  @max_line_length.setter
  def max_line_length(self, max_line_length):
    self.max_line_length_ = max_line_length

  @property
  def text(self):
    return self.data_[-1].getvalue()

  @property
  def utf8_text(self):
    return self.data_[-1].getvalue().encode('utf-8')

  @v.on('node')
  def visit(self, node):
    """
    This is the generic method that initializes the
    dynamic dispatcher.
    """

  @v.when(Node)
  def visit(self, node):
    """
    Will run for nodes that do specifically match the
    provided type.
    """
    is_empty = (node.text is None) and (len(node.children) == 0)
    open_tag, close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    self.write_data(open_tag)
    if node.text is not None:
      self.write_data(node.text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    self.write_data(close_tag)
    if node.tail is not None:
      self.write_data(node.tail)

  '''[[[cog
  upperFirst = lambda s: s[:1].upper() + s[1:] if s else ''
  for namespace, tag, open_tag, preclose_tag, close_tag, node_text, post_tag, indent_char, attributes, actions in tags:
    node_ns   = upperFirst(namespace.split('/')[-1])
    node_name = upperFirst(tag.replace('-', ''))
    if open_tag.endswith(")"):
      pass
    elif open_tag.startswith("f\""):
      open_tag = 'open_tag = ' + open_tag
    elif open_tag == "~default~":
      open_tag = 'open_tag = None'
    else:
      open_tag = 'open_tag = """' + open_tag + '"""'
    if close_tag == "~ignore~" or (close_tag.find("(") != -1 and close_tag.endswith(")")):
      if close_tag == "~ignore~":
        close_tag = ''
    elif close_tag == "~default~":
      close_tag = 'close_tag = None'
    elif close_tag.startswith("f\""):
      close_tag = 'close_tag = ' + close_tag
    else:
      close_tag = 'close_tag = """' + close_tag + '"""'
    if node_text.endswith(")"):
      pass
    else:
      node_text = 'node_text = node.text'
    attr_str = ""
    if len(attributes) > 0:  
      attr_list = attributes.split("|")
      attr_indent = ""
      for attr in attr_list:
        attr_str += attr_indent + "attr_" + attr + " = node.attribute(\"" + attr + "\")\n"
        attr_indent = "  "

    if actions == "contents":
      cog.outl("""@v.when(%s%sNode)
  def visit(self, node):
    # Matches nodes of type %s%sNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    %s
    %s
    %s
    %s
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    %s
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    %s
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      """ % (node_ns, node_name, node_ns, node_name, attr_str, open_tag, close_tag, node_text, preclose_tag, post_tag,))
    elif actions == "ignore":
      cog.outl("""@v.when(%s%sNode)
  def visit(self, node):
    # Matches nodes of type %s%sNode
    if node.tail is not None:
      self.write_data(node.tail)
      """ % (node_ns, node_name, node_ns, node_name,))
    else:
      cog.outl("""# ERROR: Uknnown action for nodes of type %sNode
      """ % (upperFirst(node_name),))

  ]]]'''
  @v.when(XhtmlCommentNode)
  def visit(self, node):
    # Matches nodes of type XhtmlCommentNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_comment_tag(node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlHtmlNode)
  def visit(self, node):
    # Matches nodes of type XhtmlHtmlNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlBaseNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBaseNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_href = node.attribute("href")

    open_tag, close_tag = self.format_base_tag(attr_href)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlHeadNode)
  def visit(self, node):
    # Matches nodes of type XhtmlHeadNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlLinkNode)
  def visit(self, node):
    # Matches nodes of type XhtmlLinkNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlMetaNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMetaNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlStyleNode)
  def visit(self, node):
    # Matches nodes of type XhtmlStyleNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlTitleNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTitleNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_title_tag(node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlBodyNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBodyNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlAddressNode)
  def visit(self, node):
    # Matches nodes of type XhtmlAddressNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlArticleNode)
  def visit(self, node):
    # Matches nodes of type XhtmlArticleNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlAsideNode)
  def visit(self, node):
    # Matches nodes of type XhtmlAsideNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlFooterNode)
  def visit(self, node):
    # Matches nodes of type XhtmlFooterNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlHeaderNode)
  def visit(self, node):
    # Matches nodes of type XhtmlHeaderNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """

  """
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlH1Node)
  def visit(self, node):
    # Matches nodes of type XhtmlH1Node
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """# """
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlH2Node)
  def visit(self, node):
    # Matches nodes of type XhtmlH2Node
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """## """
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlH3Node)
  def visit(self, node):
    # Matches nodes of type XhtmlH3Node
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """### """
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlH4Node)
  def visit(self, node):
    # Matches nodes of type XhtmlH4Node
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """#### """
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlH5Node)
  def visit(self, node):
    # Matches nodes of type XhtmlH5Node
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """##### """
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlH6Node)
  def visit(self, node):
    # Matches nodes of type XhtmlH6Node
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """###### """
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlHgroupNode)
  def visit(self, node):
    # Matches nodes of type XhtmlHgroupNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlMainNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMainNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlNavNode)
  def visit(self, node):
    # Matches nodes of type XhtmlNavNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSectionNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSectionNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlBlockquoteNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBlockquoteNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_blockquote_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_blockquote_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    node_preclose = self.preclose_blockquote_tag()
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_blockquote_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDdNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDdNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_dd_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_dd_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_dd_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDivNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDivNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_div_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_div_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDlNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDlNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_dl_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_dl_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_dl_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDtNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDtNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_dt_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_dt_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_dt_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlFigcaptionNode)
  def visit(self, node):
    # Matches nodes of type XhtmlFigcaptionNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlFigureNode)
  def visit(self, node):
    # Matches nodes of type XhtmlFigureNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlHrNode)
  def visit(self, node):
    # Matches nodes of type XhtmlHrNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """
  ---
  """
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlLiNode)
  def visit(self, node):
    # Matches nodes of type XhtmlLiNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_li_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_li_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_li_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlMainNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMainNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlOlNode)
  def visit(self, node):
    # Matches nodes of type XhtmlOlNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_ol_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_ol_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_ol_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlPNode)
  def visit(self, node):
    # Matches nodes of type XhtmlPNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_p_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_p_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlPreNode)
  def visit(self, node):
    # Matches nodes of type XhtmlPreNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_language = node.attribute("language")
    attr_class = node.attribute("class")

    open_tag, close_tag = self.format_pre_tag(attr_language, attr_class, node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.close_pre_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlUlNode)
  def visit(self, node):
    # Matches nodes of type XhtmlUlNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_ul_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_ul_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_ul_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlANode)
  def visit(self, node):
    # Matches nodes of type XhtmlANode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_text = node.attribute("text")
    attr_href = node.attribute("href")
    attr_title = node.attribute("title")

    open_tag, close_tag =self.format_link(attr_text, attr_href, attr_title)
    
    node_text, node_tail = self.format_link_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlAbbrNode)
  def visit(self, node):
    # Matches nodes of type XhtmlAbbrNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_title = node.attribute("title")

    open_tag, close_tag = self.format_abbr_tag(attr_title)
    
    node_text, node_pre_tag = self.format_abbr_text(attr_title, node.text)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlBNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """**"""
    close_tag = """**"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlBdiNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBdiNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlBdoNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBdoNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlBrNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBrNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_br_tag(node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlCiteNode)
  def visit(self, node):
    # Matches nodes of type XhtmlCiteNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlCodeNode)
  def visit(self, node):
    # Matches nodes of type XhtmlCodeNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_lang = node.attribute("lang")
    attr_class = node.attribute("class")

    open_tag, close_tag = self.format_code_tag(attr_lang, attr_class, node.text)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.close_code_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDataNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDataNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDfnNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDfnNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlEmNode)
  def visit(self, node):
    # Matches nodes of type XhtmlEmNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """*"""
    close_tag = """*"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlINode)
  def visit(self, node):
    # Matches nodes of type XhtmlINode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """*"""
    close_tag = """*"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlKbdNode)
  def visit(self, node):
    # Matches nodes of type XhtmlKbdNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlMarkNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMarkNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlQNode)
  def visit(self, node):
    # Matches nodes of type XhtmlQNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlRbNode)
  def visit(self, node):
    # Matches nodes of type XhtmlRbNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlRpNode)
  def visit(self, node):
    # Matches nodes of type XhtmlRpNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlRtNode)
  def visit(self, node):
    # Matches nodes of type XhtmlRtNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlRtcNode)
  def visit(self, node):
    # Matches nodes of type XhtmlRtcNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlRubyNode)
  def visit(self, node):
    # Matches nodes of type XhtmlRubyNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlSNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """~~"""
    close_tag = """~~"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSampNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSampNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSmallNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSmallNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSpanNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSpanNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlStrongNode)
  def visit(self, node):
    # Matches nodes of type XhtmlStrongNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """**"""
    close_tag = """**"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSubNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSubNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSupNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSupNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTimeNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTimeNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlUNode)
  def visit(self, node):
    # Matches nodes of type XhtmlUNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlVarNode)
  def visit(self, node):
    # Matches nodes of type XhtmlVarNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlWbrNode)
  def visit(self, node):
    # Matches nodes of type XhtmlWbrNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """<wbr>"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlAreaNode)
  def visit(self, node):
    # Matches nodes of type XhtmlAreaNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlAudioNode)
  def visit(self, node):
    # Matches nodes of type XhtmlAudioNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlImgNode)
  def visit(self, node):
    # Matches nodes of type XhtmlImgNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_src = node.attribute("src")
    attr_alt = node.attribute("alt")
    attr_title = node.attribute("title")

    open_tag, close_tag = self.format_img_link(attr_src, attr_alt, attr_title)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlMapNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMapNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlTrackNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTrackNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlVideoNode)
  def visit(self, node):
    # Matches nodes of type XhtmlVideoNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlEmbedNode)
  def visit(self, node):
    # Matches nodes of type XhtmlEmbedNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlIframeNode)
  def visit(self, node):
    # Matches nodes of type XhtmlIframeNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlObjectNode)
  def visit(self, node):
    # Matches nodes of type XhtmlObjectNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlParamNode)
  def visit(self, node):
    # Matches nodes of type XhtmlParamNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlPictureNode)
  def visit(self, node):
    # Matches nodes of type XhtmlPictureNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSourceNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSourceNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlCanvasNode)
  def visit(self, node):
    # Matches nodes of type XhtmlCanvasNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlNoscriptNode)
  def visit(self, node):
    # Matches nodes of type XhtmlNoscriptNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlScriptNode)
  def visit(self, node):
    # Matches nodes of type XhtmlScriptNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlDelNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDelNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """~~"""
    close_tag = """~~"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlInsNode)
  def visit(self, node):
    # Matches nodes of type XhtmlInsNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """++"""
    close_tag = """++"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlCaptionNode)
  def visit(self, node):
    # Matches nodes of type XhtmlCaptionNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = """</caption>
  """
    node_text, node_tail = self.format_caption_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlColNode)
  def visit(self, node):
    # Matches nodes of type XhtmlColNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlColgroupNode)
  def visit(self, node):
    # Matches nodes of type XhtmlColgroupNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTableNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTableNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_table_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_table_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_table_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTbodyNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTbodyNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text, node_tail = self.format_tbody_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTdNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTdNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_style = node.attribute("style")

    open_tag = """"""
    close_tag = """|"""
    node_text, node_tail = self.format_td_text(attr_style, node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTfootNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTfootNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text, node_tail = self.format_tfoot_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlThNode)
  def visit(self, node):
    # Matches nodes of type XhtmlThNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_style = node.attribute("style")
    attr_align = node.attribute("align")

    open_tag, close_tag = self.format_th_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_th_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    node_preclose = self.preclose_th_tag(attr_style, attr_align, node.text, node.tail)
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTheadNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTheadNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_thead_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_thead_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    node_preclose = self.preclose_thead_tag()
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_thead_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTrNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTrNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_tr_tag(node.text, node.tail)
    
    node_text, node_tail = self.format_tr_text(node.text, node.tail)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    node_pre_tail = self.post_tr_tag(node)
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlButtonNode)
  def visit(self, node):
    # Matches nodes of type XhtmlButtonNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlDatalistNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDatalistNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlFieldsetNode)
  def visit(self, node):
    # Matches nodes of type XhtmlFieldsetNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlFormNode)
  def visit(self, node):
    # Matches nodes of type XhtmlFormNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlInputNode)
  def visit(self, node):
    # Matches nodes of type XhtmlInputNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_type = node.attribute("type")
    attr_checked = node.attribute("checked")

    open_tag, close_tag = self.format_input_tag(attr_type, attr_checked, node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlLabelNode)
  def visit(self, node):
    # Matches nodes of type XhtmlLabelNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlLegendNode)
  def visit(self, node):
    # Matches nodes of type XhtmlLegendNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlMeterNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMeterNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlOptgroupNode)
  def visit(self, node):
    # Matches nodes of type XhtmlOptgroupNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlOptionNode)
  def visit(self, node):
    # Matches nodes of type XhtmlOptionNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlOutputNode)
  def visit(self, node):
    # Matches nodes of type XhtmlOutputNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlProgressNode)
  def visit(self, node):
    # Matches nodes of type XhtmlProgressNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlSelectNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSelectNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTextareaNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTextareaNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDetailsNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDetailsNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDialogNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDialogNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlMenuNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMenuNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSummaryNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSummaryNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSlotNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSlotNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTemplateNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTemplateNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlAcronymNode)
  def visit(self, node):
    # Matches nodes of type XhtmlAcronymNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_title = node.attribute("title")

    open_tag, close_tag = self.format_abbr_tag(attr_title)
    
    node_text, node_pre_tag = self.format_abbr_text(attr_title, node.text)
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlAppletNode)
  def visit(self, node):
    # Matches nodes of type XhtmlAppletNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlBasefontNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBasefontNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlBgsoundNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBgsoundNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlBigNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBigNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlBlinkNode)
  def visit(self, node):
    # Matches nodes of type XhtmlBlinkNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlCenterNode)
  def visit(self, node):
    # Matches nodes of type XhtmlCenterNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlCommandNode)
  def visit(self, node):
    # Matches nodes of type XhtmlCommandNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlContentNode)
  def visit(self, node):
    # Matches nodes of type XhtmlContentNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlDirNode)
  def visit(self, node):
    # Matches nodes of type XhtmlDirNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlElementNode)
  def visit(self, node):
    # Matches nodes of type XhtmlElementNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlFontNode)
  def visit(self, node):
    # Matches nodes of type XhtmlFontNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlFrameNode)
  def visit(self, node):
    # Matches nodes of type XhtmlFrameNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlFramesetNode)
  def visit(self, node):
    # Matches nodes of type XhtmlFramesetNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlImageNode)
  def visit(self, node):
    # Matches nodes of type XhtmlImageNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlIsindexNode)
  def visit(self, node):
    # Matches nodes of type XhtmlIsindexNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlKeygenNode)
  def visit(self, node):
    # Matches nodes of type XhtmlKeygenNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlListingNode)
  def visit(self, node):
    # Matches nodes of type XhtmlListingNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlMarqueeNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMarqueeNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlMenuitemNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMenuitemNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlMulticolNode)
  def visit(self, node):
    # Matches nodes of type XhtmlMulticolNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlNextidNode)
  def visit(self, node):
    # Matches nodes of type XhtmlNextidNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlNobrNode)
  def visit(self, node):
    # Matches nodes of type XhtmlNobrNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlNoembedNode)
  def visit(self, node):
    # Matches nodes of type XhtmlNoembedNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlNoframesNode)
  def visit(self, node):
    # Matches nodes of type XhtmlNoframesNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """"""
    close_tag = """"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlPlaintextNode)
  def visit(self, node):
    # Matches nodes of type XhtmlPlaintextNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlShadowNode)
  def visit(self, node):
    # Matches nodes of type XhtmlShadowNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSpacerNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSpacerNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlStrikeNode)
  def visit(self, node):
    # Matches nodes of type XhtmlStrikeNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = """~~"""
    close_tag = """~~"""
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlTtNode)
  def visit(self, node):
    # Matches nodes of type XhtmlTtNode
    if node.tail is not None:
      self.write_data(node.tail)
      
  @v.when(XhtmlXmpNode)
  def visit(self, node):
    # Matches nodes of type XhtmlXmpNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XhtmlSvgNode)
  def visit(self, node):
    # Matches nodes of type XhtmlSvgNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_svg_tag(node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_svg_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgANode)
  def visit(self, node):
    # Matches nodes of type SvgANode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgAnimateNode)
  def visit(self, node):
    # Matches nodes of type SvgAnimateNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgAnimateMotionNode)
  def visit(self, node):
    # Matches nodes of type SvgAnimateMotionNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgAnimateTransformNode)
  def visit(self, node):
    # Matches nodes of type SvgAnimateTransformNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgCircleNode)
  def visit(self, node):
    # Matches nodes of type SvgCircleNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgClipPathNode)
  def visit(self, node):
    # Matches nodes of type SvgClipPathNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgColorprofileNode)
  def visit(self, node):
    # Matches nodes of type SvgColorprofileNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgDefsNode)
  def visit(self, node):
    # Matches nodes of type SvgDefsNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgDescNode)
  def visit(self, node):
    # Matches nodes of type SvgDescNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgDiscardNode)
  def visit(self, node):
    # Matches nodes of type SvgDiscardNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgEllipseNode)
  def visit(self, node):
    # Matches nodes of type SvgEllipseNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeBlendNode)
  def visit(self, node):
    # Matches nodes of type SvgFeBlendNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeColorMatrixNode)
  def visit(self, node):
    # Matches nodes of type SvgFeColorMatrixNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeComponentTransferNode)
  def visit(self, node):
    # Matches nodes of type SvgFeComponentTransferNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeCompositeNode)
  def visit(self, node):
    # Matches nodes of type SvgFeCompositeNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeConvolveMatrixNode)
  def visit(self, node):
    # Matches nodes of type SvgFeConvolveMatrixNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeDiffuseLightingNode)
  def visit(self, node):
    # Matches nodes of type SvgFeDiffuseLightingNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeDisplacementMapNode)
  def visit(self, node):
    # Matches nodes of type SvgFeDisplacementMapNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeDistantLightNode)
  def visit(self, node):
    # Matches nodes of type SvgFeDistantLightNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeDropShadowNode)
  def visit(self, node):
    # Matches nodes of type SvgFeDropShadowNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeFloodNode)
  def visit(self, node):
    # Matches nodes of type SvgFeFloodNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeFuncANode)
  def visit(self, node):
    # Matches nodes of type SvgFeFuncANode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeFuncBNode)
  def visit(self, node):
    # Matches nodes of type SvgFeFuncBNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeFuncGNode)
  def visit(self, node):
    # Matches nodes of type SvgFeFuncGNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeFuncRNode)
  def visit(self, node):
    # Matches nodes of type SvgFeFuncRNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeGaussianBlurNode)
  def visit(self, node):
    # Matches nodes of type SvgFeGaussianBlurNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeImageNode)
  def visit(self, node):
    # Matches nodes of type SvgFeImageNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeMergeNode)
  def visit(self, node):
    # Matches nodes of type SvgFeMergeNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeMergeNodeNode)
  def visit(self, node):
    # Matches nodes of type SvgFeMergeNodeNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeMorphologyNode)
  def visit(self, node):
    # Matches nodes of type SvgFeMorphologyNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeOffsetNode)
  def visit(self, node):
    # Matches nodes of type SvgFeOffsetNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFePointLightNode)
  def visit(self, node):
    # Matches nodes of type SvgFePointLightNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeSpecularLightingNode)
  def visit(self, node):
    # Matches nodes of type SvgFeSpecularLightingNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeSpotLightNode)
  def visit(self, node):
    # Matches nodes of type SvgFeSpotLightNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeTileNode)
  def visit(self, node):
    # Matches nodes of type SvgFeTileNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFeTurbulenceNode)
  def visit(self, node):
    # Matches nodes of type SvgFeTurbulenceNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgFilterNode)
  def visit(self, node):
    # Matches nodes of type SvgFilterNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgForeignObjectNode)
  def visit(self, node):
    # Matches nodes of type SvgForeignObjectNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgGNode)
  def visit(self, node):
    # Matches nodes of type SvgGNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgHatchNode)
  def visit(self, node):
    # Matches nodes of type SvgHatchNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgHatchpathNode)
  def visit(self, node):
    # Matches nodes of type SvgHatchpathNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgImageNode)
  def visit(self, node):
    # Matches nodes of type SvgImageNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgLineNode)
  def visit(self, node):
    # Matches nodes of type SvgLineNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgLinearGradientNode)
  def visit(self, node):
    # Matches nodes of type SvgLinearGradientNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgMarkerNode)
  def visit(self, node):
    # Matches nodes of type SvgMarkerNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgMaskNode)
  def visit(self, node):
    # Matches nodes of type SvgMaskNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgMeshNode)
  def visit(self, node):
    # Matches nodes of type SvgMeshNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgMeshgradientNode)
  def visit(self, node):
    # Matches nodes of type SvgMeshgradientNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgMeshpatchNode)
  def visit(self, node):
    # Matches nodes of type SvgMeshpatchNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgMeshrowNode)
  def visit(self, node):
    # Matches nodes of type SvgMeshrowNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgMetadataNode)
  def visit(self, node):
    # Matches nodes of type SvgMetadataNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgMpathNode)
  def visit(self, node):
    # Matches nodes of type SvgMpathNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgPathNode)
  def visit(self, node):
    # Matches nodes of type SvgPathNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgPatternNode)
  def visit(self, node):
    # Matches nodes of type SvgPatternNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgPolygonNode)
  def visit(self, node):
    # Matches nodes of type SvgPolygonNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgPolylineNode)
  def visit(self, node):
    # Matches nodes of type SvgPolylineNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgRadialGradientNode)
  def visit(self, node):
    # Matches nodes of type SvgRadialGradientNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgRectNode)
  def visit(self, node):
    # Matches nodes of type SvgRectNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgScriptNode)
  def visit(self, node):
    # Matches nodes of type SvgScriptNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgSetNode)
  def visit(self, node):
    # Matches nodes of type SvgSetNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgSolidcolorNode)
  def visit(self, node):
    # Matches nodes of type SvgSolidcolorNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgStopNode)
  def visit(self, node):
    # Matches nodes of type SvgStopNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgStyleNode)
  def visit(self, node):
    # Matches nodes of type SvgStyleNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgSvgNode)
  def visit(self, node):
    # Matches nodes of type SvgSvgNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_svg_tag(node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_svg_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgSwitchNode)
  def visit(self, node):
    # Matches nodes of type SvgSwitchNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgSymbolNode)
  def visit(self, node):
    # Matches nodes of type SvgSymbolNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgTextNode)
  def visit(self, node):
    # Matches nodes of type SvgTextNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgTextPathNode)
  def visit(self, node):
    # Matches nodes of type SvgTextPathNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgTitleNode)
  def visit(self, node):
    # Matches nodes of type SvgTitleNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgTspanNode)
  def visit(self, node):
    # Matches nodes of type SvgTspanNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgUnknownNode)
  def visit(self, node):
    # Matches nodes of type SvgUnknownNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgUseNode)
  def visit(self, node):
    # Matches nodes of type SvgUseNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(SvgViewNode)
  def visit(self, node):
    # Matches nodes of type SvgViewNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMathNode)
  def visit(self, node):
    # Matches nodes of type MathMLMathNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag, close_tag = self.format_math_tag(node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    self.post_math_tag()
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMactionNode)
  def visit(self, node):
    # Matches nodes of type MathMLMactionNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMaligngroupNode)
  def visit(self, node):
    # Matches nodes of type MathMLMaligngroupNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMalignmarkNode)
  def visit(self, node):
    # Matches nodes of type MathMLMalignmarkNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMencloseNode)
  def visit(self, node):
    # Matches nodes of type MathMLMencloseNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMerrorNode)
  def visit(self, node):
    # Matches nodes of type MathMLMerrorNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMfencedNode)
  def visit(self, node):
    # Matches nodes of type MathMLMfencedNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMfracNode)
  def visit(self, node):
    # Matches nodes of type MathMLMfracNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMglyphNode)
  def visit(self, node):
    # Matches nodes of type MathMLMglyphNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMiNode)
  def visit(self, node):
    # Matches nodes of type MathMLMiNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMlabeledtrNode)
  def visit(self, node):
    # Matches nodes of type MathMLMlabeledtrNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMlongdivNode)
  def visit(self, node):
    # Matches nodes of type MathMLMlongdivNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMmultiscriptsNode)
  def visit(self, node):
    # Matches nodes of type MathMLMmultiscriptsNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMnNode)
  def visit(self, node):
    # Matches nodes of type MathMLMnNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMoNode)
  def visit(self, node):
    # Matches nodes of type MathMLMoNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMoverNode)
  def visit(self, node):
    # Matches nodes of type MathMLMoverNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMpaddedNode)
  def visit(self, node):
    # Matches nodes of type MathMLMpaddedNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMphantomNode)
  def visit(self, node):
    # Matches nodes of type MathMLMphantomNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMrootNode)
  def visit(self, node):
    # Matches nodes of type MathMLMrootNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMrowNode)
  def visit(self, node):
    # Matches nodes of type MathMLMrowNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMsNode)
  def visit(self, node):
    # Matches nodes of type MathMLMsNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMscarriesNode)
  def visit(self, node):
    # Matches nodes of type MathMLMscarriesNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMscarryNode)
  def visit(self, node):
    # Matches nodes of type MathMLMscarryNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMsgroupNode)
  def visit(self, node):
    # Matches nodes of type MathMLMsgroupNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMslineNode)
  def visit(self, node):
    # Matches nodes of type MathMLMslineNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMspaceNode)
  def visit(self, node):
    # Matches nodes of type MathMLMspaceNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMsqrtNode)
  def visit(self, node):
    # Matches nodes of type MathMLMsqrtNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMsrowNode)
  def visit(self, node):
    # Matches nodes of type MathMLMsrowNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMstackNode)
  def visit(self, node):
    # Matches nodes of type MathMLMstackNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMstyleNode)
  def visit(self, node):
    # Matches nodes of type MathMLMstyleNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMsubNode)
  def visit(self, node):
    # Matches nodes of type MathMLMsubNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMsupNode)
  def visit(self, node):
    # Matches nodes of type MathMLMsupNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMsubsupNode)
  def visit(self, node):
    # Matches nodes of type MathMLMsubsupNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMtableNode)
  def visit(self, node):
    # Matches nodes of type MathMLMtableNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMtdNode)
  def visit(self, node):
    # Matches nodes of type MathMLMtdNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMtextNode)
  def visit(self, node):
    # Matches nodes of type MathMLMtextNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMtrNode)
  def visit(self, node):
    # Matches nodes of type MathMLMtrNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMunderNode)
  def visit(self, node):
    # Matches nodes of type MathMLMunderNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLMunderoverNode)
  def visit(self, node):
    # Matches nodes of type MathMLMunderoverNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLSemanticsNode)
  def visit(self, node):
    # Matches nodes of type MathMLSemanticsNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLAnnotationNode)
  def visit(self, node):
    # Matches nodes of type MathMLAnnotationNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(MathMLAnnotationxmlNode)
  def visit(self, node):
    # Matches nodes of type MathMLAnnotationxmlNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    
    open_tag = None
    close_tag = None
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  @v.when(XmlnsXML_DECLNode)
  def visit(self, node):
    # Matches nodes of type XmlnsXML_DECLNode
    is_empty = (node.text is None) and (len(node.children) == 0)
    html_open_tag, html_close_tag = format_html_tag(
      node.name, node.attributes, self.indent_, self.indent_char_[-1],
      self.max_line_length_, is_empty, node.text, node.tail, self.newline_char_)
    node_text = node.text
    node_tail = node.tail
    node_pre_tag  = None
    node_pre_tail = None
    node_preclose = None
    attr_version = node.attribute("version")
    attr_encoding = node.attribute("encoding")
    attr_standalone = node.attribute("standalone")

    open_tag, close_tag = self.format_XML_DECL_tag(attr_version, attr_encoding, attr_standalone, node.text, node.tail)
    
    node_text = node.text
    if open_tag is None:
      open_tag = html_open_tag
    if close_tag is None:
      close_tag = html_close_tag
    if node_pre_tag is not None:
      self.write_data(node_pre_tag)
    if len(open_tag) > 0:
      self.write_data(open_tag)
    if node_text is not None:
      self.write_data(node_text)
    self.indent_ += 1
    for n in node.children:
      self.visit(n)
    self.indent_ -= 1
    
    if node_preclose is not None:
      self.write_data(node_preclose)
    if len(close_tag) > 0:
      self.write_data(close_tag)
    
    if node_pre_tail is not None:
      self.write_data(node_pre_tail)
    if node_tail is not None:
      self.write_data(node_tail)
      
  #[[[end]]]  
  
  # @v.when(AssignmentExpression)
  # def visit(self, node):
  #   """ Matches nodes of type AssignmentExpression. """
  #   node.children[0].accept(self)
  #   sys.stdout.write('=')
  #   node.children[1].accept(self)

  # @v.when(VariableNode)
  # def visit(self, node):
  #   """ Matches nodes that contain variables. """
  #   sys.stdout.write(str(node.name))

  # @v.when(Literal)
  # def visit(self, node):
  #   """ Matches nodes that contain literal values. """
  #   sys.stdout.write(str(node.value))

