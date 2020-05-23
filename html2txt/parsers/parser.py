import os
import re
import html5lib
#import html5_parser
import xml
from html2txt import parsers

import html
from html.parser import HTMLParser
from xml.etree import ElementTree

from html5lib.treebuilders import getTreeBuilder

from .etreehtmlparser import ETreeHTMLParser

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

XML_NS = "http://www.w3.org/2000/xmlns"
XHTML_NS = "http://www.w3.org/1999/xhtml"
SVG_NS = "http://www.w3.org/2000/svg"
MATHML_NS = "http://www.w3.org/1998/Math/MathML"

def _xmlns(tag):
  return '{%s}%s' % (XML_NS, tag)

def _xhtmlns(tag):
  return '{%s}%s' % (XHTML_NS, tag)

def _svgns(tag):
  return '{%s}%s' % (SVG_NS, tag)

def _mathmlns(tag):
  return '{%s}%s' % (MATHML_NS, tag)

def whitespace_to_space(s):
  if s is None:
    return s
  t = s.replace('\t', ' ')
  t = s.replace('\n', ' ')
  t = t.replace('\r', ' ')
  t = t.replace('\v', ' ')
  t = t.replace('\x0b', ' ')
  t = t.replace('\f', ' ')
  t = t.replace('\x0c', ' ')
  t = t.replace('\x1c', ' ')
  t = t.replace('\x1d', ' ')
  t = t.replace('\x1e', ' ')
  t = t.replace('\x85', ' ')
  t = t.replace('\u2028', ' ')
  t = t.replace('\u2029', ' ')
  return t


class HtmlParser:
  def __init__(self):
    self.tree_ = None
    self.namespace_map_ = {}

    # https://nedbatchelder.com/code/cog/
    # cog -r parser.py
    '''[[[cog
    import cog

    xml_tags = [
      "XML_DECL",
    ]

    svg_tags = [
      "a",
      "animate",
      "animateMotion",
      "animateTransform",
      "circle",
      "clipPath",
      "color-profile",
      "defs",
      "desc",
      "discard",
      "ellipse",
      "feBlend",
      "feColorMatrix",
      "feComponentTransfer",
      "feComposite",
      "feConvolveMatrix",
      "feDiffuseLighting",
      "feDisplacementMap",
      "feDistantLight",
      "feDropShadow",
      "feFlood",
      "feFuncA",
      "feFuncB",
      "feFuncG",
      "feFuncR",
      "feGaussianBlur",
      "feImage",
      "feMerge",
      "feMergeNode",
      "feMorphology",
      "feOffset",
      "fePointLight",
      "feSpecularLighting",
      "feSpotLight",
      "feTile",
      "feTurbulence",
      "filter",
      "foreignObject",
      "g",
      "hatch",
      "hatchpath",
      "image",
      "line",
      "linearGradient",
      "marker",
      "mask",
      "mesh",
      "meshgradient",
      "meshpatch",
      "meshrow",
      "metadata",
      "mpath",
      "path",
      "pattern",
      "polygon",
      "polyline",
      "radialGradient",
      "rect",
      "script",
      "set",
      "solidcolor",
      "stop",
      "style",
      "svg",
      "switch",
      "symbol",
      "text",
      "textPath",
      "title",
      "tspan",
      "unknown",
      "use",
      "view",
    ]

    mathml_tags = [
      "math",
      "maction",
      "maligngroup",
      "malignmark",
      "menclose",
      "merror",
      "mfenced",
      "mfrac",
      "mglyph",
      "mi",
      "mlabeledtr",
      "mlongdiv",
      "mmultiscripts",
      "mn",
      "mo",
      "mover",
      "mpadded",
      "mphantom",
      "mroot",
      "mrow",
      "ms",
      "mscarries",
      "mscarry",
      "msgroup",
      "msline",
      "mspace",
      "msqrt",
      "msrow",
      "mstack",
      "mstyle",
      "msub",
      "msup",
      "msubsup",
      "mtable",
      "mtd",
      "mtext",
      "mtr",
      "munder",
      "munderover",
      "semantics",
      "annotation",
      "annotation-xml",      
    ]

    xhtml_tags = [
      "comment",
      "html",
      "base",
      "head",
      "link",
      "meta",
      "style",
      "title",
      "body",
      "address",
      "article",
      "aside",
      "footer",
      "header",
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "hgroup",
      "main",
      "nav",
      "section",
      "blockquote",
      "dd",
      "div",
      "dl",
      "dt",
      "figcaption",
      "figure",
      "hr",
      "li",
      "ol",
      "p",
      "pre",
      "ul",
      "a",
      "abbr",
      "b",
      "bdi",
      "bdo",
      "br",
      "cite",
      "code",
      "data",
      "dfn",
      "em",
      "i",
      "kbd",
      "mark",
      "q",
      "rb",
      "rp",
      "rt",
      "rtc",
      "ruby",
      "s",
      "samp",
      "small",
      "span",
      "strong",
      "sub",
      "sup",
      "time",
      "u",
      "var",
      "wbr",
      "area",
      "audio",
      "img",
      "map",
      "track",
      "video",
      "embed",
      "iframe",
      "object",
      "param",
      "picture",
      "source",
      "canvas",
      "noscript",
      "script",
      "del",
      "ins",
      "caption",
      "col",
      "colgroup",
      "table",
      "tbody",
      "td",
      "tfoot",
      "th",
      "thead",
      "tr",
      "button",
      "datalist",
      "fieldset",
      "form",
      "input",
      "label",
      "legend",
      "meter",
      "optgroup",
      "option",
      "output",
      "progress",
      "select",
      "textarea",
      "details",
      "dialog",
      "menu",
      "summary",
      "slot",
      "template",
      "acronym",
      "applet",
      "basefont",
      "bgsound",
      "big",
      "blink",
      "center",
      "command",
      "content",
      "dir",
      "element",
      "font",
      "frame",
      "frameset",
      "image",
      "isindex",
      "keygen",
      "listing",
      "marquee",
      "menuitem",
      "multicol",
      "nextid",
      "nobr",
      "noembed",
      "noframes",
      "plaintext",
      "shadow",
      "spacer",
      "strike",
      "tt",
      "xmp",
      "svg",
    ]
    XML_NS = "http://www.w3.org/2000/xmlns"
    XHTML_NS = "http://www.w3.org/1999/xhtml"
    SVG_NS = "http://www.w3.org/2000/svg"
    MATHML_NS = "http://www.w3.org/1998/Math/MathML"
    upperFirst = lambda s: s[:1].upper() + s[1:] if s else ''
    cog.outl("""self.parser_methods = {""")
    for tag in xhtml_tags:
      namespace = XHTML_NS
      node_ns   = upperFirst(namespace.split('/')[-1])
      node_name = upperFirst(tag.replace('-', ''))
      cog.outl("  '{%s}%s': self._parse_%s_%s, " % (namespace, tag, node_ns, node_name,))
    for tag in svg_tags:
      namespace = SVG_NS
      node_ns   = upperFirst(namespace.split('/')[-1])
      node_name = upperFirst(tag.replace('-', ''))
      cog.outl("  '{%s}%s': self._parse_%s_%s, " % (namespace, tag, node_ns, node_name,))
    for tag in mathml_tags:
      namespace = MATHML_NS
      node_ns   = upperFirst(namespace.split('/')[-1])
      node_name = upperFirst(tag.replace('-', ''))
      cog.outl("  '{%s}%s': self._parse_%s_%s, " % (namespace, tag, node_ns, node_name,))
    for tag in xml_tags:
      namespace = XML_NS
      node_ns   = upperFirst(namespace.split('/')[-1])
      node_name = upperFirst(tag.replace('-', ''))
      cog.outl("  '{%s}%s': self._parse_%s_%s, " % (namespace, tag, node_ns, node_name,))
    cog.outl("}")
    ]]]'''
    self.parser_methods = {
      '{http://www.w3.org/1999/xhtml}comment': self._parse_Xhtml_Comment, 
      '{http://www.w3.org/1999/xhtml}html': self._parse_Xhtml_Html, 
      '{http://www.w3.org/1999/xhtml}base': self._parse_Xhtml_Base, 
      '{http://www.w3.org/1999/xhtml}head': self._parse_Xhtml_Head, 
      '{http://www.w3.org/1999/xhtml}link': self._parse_Xhtml_Link, 
      '{http://www.w3.org/1999/xhtml}meta': self._parse_Xhtml_Meta, 
      '{http://www.w3.org/1999/xhtml}style': self._parse_Xhtml_Style, 
      '{http://www.w3.org/1999/xhtml}title': self._parse_Xhtml_Title, 
      '{http://www.w3.org/1999/xhtml}body': self._parse_Xhtml_Body, 
      '{http://www.w3.org/1999/xhtml}address': self._parse_Xhtml_Address, 
      '{http://www.w3.org/1999/xhtml}article': self._parse_Xhtml_Article, 
      '{http://www.w3.org/1999/xhtml}aside': self._parse_Xhtml_Aside, 
      '{http://www.w3.org/1999/xhtml}footer': self._parse_Xhtml_Footer, 
      '{http://www.w3.org/1999/xhtml}header': self._parse_Xhtml_Header, 
      '{http://www.w3.org/1999/xhtml}h1': self._parse_Xhtml_H1, 
      '{http://www.w3.org/1999/xhtml}h2': self._parse_Xhtml_H2, 
      '{http://www.w3.org/1999/xhtml}h3': self._parse_Xhtml_H3, 
      '{http://www.w3.org/1999/xhtml}h4': self._parse_Xhtml_H4, 
      '{http://www.w3.org/1999/xhtml}h5': self._parse_Xhtml_H5, 
      '{http://www.w3.org/1999/xhtml}h6': self._parse_Xhtml_H6, 
      '{http://www.w3.org/1999/xhtml}hgroup': self._parse_Xhtml_Hgroup, 
      '{http://www.w3.org/1999/xhtml}main': self._parse_Xhtml_Main, 
      '{http://www.w3.org/1999/xhtml}nav': self._parse_Xhtml_Nav, 
      '{http://www.w3.org/1999/xhtml}section': self._parse_Xhtml_Section, 
      '{http://www.w3.org/1999/xhtml}blockquote': self._parse_Xhtml_Blockquote, 
      '{http://www.w3.org/1999/xhtml}dd': self._parse_Xhtml_Dd, 
      '{http://www.w3.org/1999/xhtml}div': self._parse_Xhtml_Div, 
      '{http://www.w3.org/1999/xhtml}dl': self._parse_Xhtml_Dl, 
      '{http://www.w3.org/1999/xhtml}dt': self._parse_Xhtml_Dt, 
      '{http://www.w3.org/1999/xhtml}figcaption': self._parse_Xhtml_Figcaption, 
      '{http://www.w3.org/1999/xhtml}figure': self._parse_Xhtml_Figure, 
      '{http://www.w3.org/1999/xhtml}hr': self._parse_Xhtml_Hr, 
      '{http://www.w3.org/1999/xhtml}li': self._parse_Xhtml_Li, 
      '{http://www.w3.org/1999/xhtml}ol': self._parse_Xhtml_Ol, 
      '{http://www.w3.org/1999/xhtml}p': self._parse_Xhtml_P, 
      '{http://www.w3.org/1999/xhtml}pre': self._parse_Xhtml_Pre, 
      '{http://www.w3.org/1999/xhtml}ul': self._parse_Xhtml_Ul, 
      '{http://www.w3.org/1999/xhtml}a': self._parse_Xhtml_A, 
      '{http://www.w3.org/1999/xhtml}abbr': self._parse_Xhtml_Abbr, 
      '{http://www.w3.org/1999/xhtml}b': self._parse_Xhtml_B, 
      '{http://www.w3.org/1999/xhtml}bdi': self._parse_Xhtml_Bdi, 
      '{http://www.w3.org/1999/xhtml}bdo': self._parse_Xhtml_Bdo, 
      '{http://www.w3.org/1999/xhtml}br': self._parse_Xhtml_Br, 
      '{http://www.w3.org/1999/xhtml}cite': self._parse_Xhtml_Cite, 
      '{http://www.w3.org/1999/xhtml}code': self._parse_Xhtml_Code, 
      '{http://www.w3.org/1999/xhtml}data': self._parse_Xhtml_Data, 
      '{http://www.w3.org/1999/xhtml}dfn': self._parse_Xhtml_Dfn, 
      '{http://www.w3.org/1999/xhtml}em': self._parse_Xhtml_Em, 
      '{http://www.w3.org/1999/xhtml}i': self._parse_Xhtml_I, 
      '{http://www.w3.org/1999/xhtml}kbd': self._parse_Xhtml_Kbd, 
      '{http://www.w3.org/1999/xhtml}mark': self._parse_Xhtml_Mark, 
      '{http://www.w3.org/1999/xhtml}q': self._parse_Xhtml_Q, 
      '{http://www.w3.org/1999/xhtml}rb': self._parse_Xhtml_Rb, 
      '{http://www.w3.org/1999/xhtml}rp': self._parse_Xhtml_Rp, 
      '{http://www.w3.org/1999/xhtml}rt': self._parse_Xhtml_Rt, 
      '{http://www.w3.org/1999/xhtml}rtc': self._parse_Xhtml_Rtc, 
      '{http://www.w3.org/1999/xhtml}ruby': self._parse_Xhtml_Ruby, 
      '{http://www.w3.org/1999/xhtml}s': self._parse_Xhtml_S, 
      '{http://www.w3.org/1999/xhtml}samp': self._parse_Xhtml_Samp, 
      '{http://www.w3.org/1999/xhtml}small': self._parse_Xhtml_Small, 
      '{http://www.w3.org/1999/xhtml}span': self._parse_Xhtml_Span, 
      '{http://www.w3.org/1999/xhtml}strong': self._parse_Xhtml_Strong, 
      '{http://www.w3.org/1999/xhtml}sub': self._parse_Xhtml_Sub, 
      '{http://www.w3.org/1999/xhtml}sup': self._parse_Xhtml_Sup, 
      '{http://www.w3.org/1999/xhtml}time': self._parse_Xhtml_Time, 
      '{http://www.w3.org/1999/xhtml}u': self._parse_Xhtml_U, 
      '{http://www.w3.org/1999/xhtml}var': self._parse_Xhtml_Var, 
      '{http://www.w3.org/1999/xhtml}wbr': self._parse_Xhtml_Wbr, 
      '{http://www.w3.org/1999/xhtml}area': self._parse_Xhtml_Area, 
      '{http://www.w3.org/1999/xhtml}audio': self._parse_Xhtml_Audio, 
      '{http://www.w3.org/1999/xhtml}img': self._parse_Xhtml_Img, 
      '{http://www.w3.org/1999/xhtml}map': self._parse_Xhtml_Map, 
      '{http://www.w3.org/1999/xhtml}track': self._parse_Xhtml_Track, 
      '{http://www.w3.org/1999/xhtml}video': self._parse_Xhtml_Video, 
      '{http://www.w3.org/1999/xhtml}embed': self._parse_Xhtml_Embed, 
      '{http://www.w3.org/1999/xhtml}iframe': self._parse_Xhtml_Iframe, 
      '{http://www.w3.org/1999/xhtml}object': self._parse_Xhtml_Object, 
      '{http://www.w3.org/1999/xhtml}param': self._parse_Xhtml_Param, 
      '{http://www.w3.org/1999/xhtml}picture': self._parse_Xhtml_Picture, 
      '{http://www.w3.org/1999/xhtml}source': self._parse_Xhtml_Source, 
      '{http://www.w3.org/1999/xhtml}canvas': self._parse_Xhtml_Canvas, 
      '{http://www.w3.org/1999/xhtml}noscript': self._parse_Xhtml_Noscript, 
      '{http://www.w3.org/1999/xhtml}script': self._parse_Xhtml_Script, 
      '{http://www.w3.org/1999/xhtml}del': self._parse_Xhtml_Del, 
      '{http://www.w3.org/1999/xhtml}ins': self._parse_Xhtml_Ins, 
      '{http://www.w3.org/1999/xhtml}caption': self._parse_Xhtml_Caption, 
      '{http://www.w3.org/1999/xhtml}col': self._parse_Xhtml_Col, 
      '{http://www.w3.org/1999/xhtml}colgroup': self._parse_Xhtml_Colgroup, 
      '{http://www.w3.org/1999/xhtml}table': self._parse_Xhtml_Table, 
      '{http://www.w3.org/1999/xhtml}tbody': self._parse_Xhtml_Tbody, 
      '{http://www.w3.org/1999/xhtml}td': self._parse_Xhtml_Td, 
      '{http://www.w3.org/1999/xhtml}tfoot': self._parse_Xhtml_Tfoot, 
      '{http://www.w3.org/1999/xhtml}th': self._parse_Xhtml_Th, 
      '{http://www.w3.org/1999/xhtml}thead': self._parse_Xhtml_Thead, 
      '{http://www.w3.org/1999/xhtml}tr': self._parse_Xhtml_Tr, 
      '{http://www.w3.org/1999/xhtml}button': self._parse_Xhtml_Button, 
      '{http://www.w3.org/1999/xhtml}datalist': self._parse_Xhtml_Datalist, 
      '{http://www.w3.org/1999/xhtml}fieldset': self._parse_Xhtml_Fieldset, 
      '{http://www.w3.org/1999/xhtml}form': self._parse_Xhtml_Form, 
      '{http://www.w3.org/1999/xhtml}input': self._parse_Xhtml_Input, 
      '{http://www.w3.org/1999/xhtml}label': self._parse_Xhtml_Label, 
      '{http://www.w3.org/1999/xhtml}legend': self._parse_Xhtml_Legend, 
      '{http://www.w3.org/1999/xhtml}meter': self._parse_Xhtml_Meter, 
      '{http://www.w3.org/1999/xhtml}optgroup': self._parse_Xhtml_Optgroup, 
      '{http://www.w3.org/1999/xhtml}option': self._parse_Xhtml_Option, 
      '{http://www.w3.org/1999/xhtml}output': self._parse_Xhtml_Output, 
      '{http://www.w3.org/1999/xhtml}progress': self._parse_Xhtml_Progress, 
      '{http://www.w3.org/1999/xhtml}select': self._parse_Xhtml_Select, 
      '{http://www.w3.org/1999/xhtml}textarea': self._parse_Xhtml_Textarea, 
      '{http://www.w3.org/1999/xhtml}details': self._parse_Xhtml_Details, 
      '{http://www.w3.org/1999/xhtml}dialog': self._parse_Xhtml_Dialog, 
      '{http://www.w3.org/1999/xhtml}menu': self._parse_Xhtml_Menu, 
      '{http://www.w3.org/1999/xhtml}summary': self._parse_Xhtml_Summary, 
      '{http://www.w3.org/1999/xhtml}slot': self._parse_Xhtml_Slot, 
      '{http://www.w3.org/1999/xhtml}template': self._parse_Xhtml_Template, 
      '{http://www.w3.org/1999/xhtml}acronym': self._parse_Xhtml_Acronym, 
      '{http://www.w3.org/1999/xhtml}applet': self._parse_Xhtml_Applet, 
      '{http://www.w3.org/1999/xhtml}basefont': self._parse_Xhtml_Basefont, 
      '{http://www.w3.org/1999/xhtml}bgsound': self._parse_Xhtml_Bgsound, 
      '{http://www.w3.org/1999/xhtml}big': self._parse_Xhtml_Big, 
      '{http://www.w3.org/1999/xhtml}blink': self._parse_Xhtml_Blink, 
      '{http://www.w3.org/1999/xhtml}center': self._parse_Xhtml_Center, 
      '{http://www.w3.org/1999/xhtml}command': self._parse_Xhtml_Command, 
      '{http://www.w3.org/1999/xhtml}content': self._parse_Xhtml_Content, 
      '{http://www.w3.org/1999/xhtml}dir': self._parse_Xhtml_Dir, 
      '{http://www.w3.org/1999/xhtml}element': self._parse_Xhtml_Element, 
      '{http://www.w3.org/1999/xhtml}font': self._parse_Xhtml_Font, 
      '{http://www.w3.org/1999/xhtml}frame': self._parse_Xhtml_Frame, 
      '{http://www.w3.org/1999/xhtml}frameset': self._parse_Xhtml_Frameset, 
      '{http://www.w3.org/1999/xhtml}image': self._parse_Xhtml_Image, 
      '{http://www.w3.org/1999/xhtml}isindex': self._parse_Xhtml_Isindex, 
      '{http://www.w3.org/1999/xhtml}keygen': self._parse_Xhtml_Keygen, 
      '{http://www.w3.org/1999/xhtml}listing': self._parse_Xhtml_Listing, 
      '{http://www.w3.org/1999/xhtml}marquee': self._parse_Xhtml_Marquee, 
      '{http://www.w3.org/1999/xhtml}menuitem': self._parse_Xhtml_Menuitem, 
      '{http://www.w3.org/1999/xhtml}multicol': self._parse_Xhtml_Multicol, 
      '{http://www.w3.org/1999/xhtml}nextid': self._parse_Xhtml_Nextid, 
      '{http://www.w3.org/1999/xhtml}nobr': self._parse_Xhtml_Nobr, 
      '{http://www.w3.org/1999/xhtml}noembed': self._parse_Xhtml_Noembed, 
      '{http://www.w3.org/1999/xhtml}noframes': self._parse_Xhtml_Noframes, 
      '{http://www.w3.org/1999/xhtml}plaintext': self._parse_Xhtml_Plaintext, 
      '{http://www.w3.org/1999/xhtml}shadow': self._parse_Xhtml_Shadow, 
      '{http://www.w3.org/1999/xhtml}spacer': self._parse_Xhtml_Spacer, 
      '{http://www.w3.org/1999/xhtml}strike': self._parse_Xhtml_Strike, 
      '{http://www.w3.org/1999/xhtml}tt': self._parse_Xhtml_Tt, 
      '{http://www.w3.org/1999/xhtml}xmp': self._parse_Xhtml_Xmp, 
      '{http://www.w3.org/1999/xhtml}svg': self._parse_Xhtml_Svg, 
      '{http://www.w3.org/2000/svg}a': self._parse_Svg_A, 
      '{http://www.w3.org/2000/svg}animate': self._parse_Svg_Animate, 
      '{http://www.w3.org/2000/svg}animateMotion': self._parse_Svg_AnimateMotion, 
      '{http://www.w3.org/2000/svg}animateTransform': self._parse_Svg_AnimateTransform, 
      '{http://www.w3.org/2000/svg}circle': self._parse_Svg_Circle, 
      '{http://www.w3.org/2000/svg}clipPath': self._parse_Svg_ClipPath, 
      '{http://www.w3.org/2000/svg}color-profile': self._parse_Svg_Colorprofile, 
      '{http://www.w3.org/2000/svg}defs': self._parse_Svg_Defs, 
      '{http://www.w3.org/2000/svg}desc': self._parse_Svg_Desc, 
      '{http://www.w3.org/2000/svg}discard': self._parse_Svg_Discard, 
      '{http://www.w3.org/2000/svg}ellipse': self._parse_Svg_Ellipse, 
      '{http://www.w3.org/2000/svg}feBlend': self._parse_Svg_FeBlend, 
      '{http://www.w3.org/2000/svg}feColorMatrix': self._parse_Svg_FeColorMatrix, 
      '{http://www.w3.org/2000/svg}feComponentTransfer': self._parse_Svg_FeComponentTransfer, 
      '{http://www.w3.org/2000/svg}feComposite': self._parse_Svg_FeComposite, 
      '{http://www.w3.org/2000/svg}feConvolveMatrix': self._parse_Svg_FeConvolveMatrix, 
      '{http://www.w3.org/2000/svg}feDiffuseLighting': self._parse_Svg_FeDiffuseLighting, 
      '{http://www.w3.org/2000/svg}feDisplacementMap': self._parse_Svg_FeDisplacementMap, 
      '{http://www.w3.org/2000/svg}feDistantLight': self._parse_Svg_FeDistantLight, 
      '{http://www.w3.org/2000/svg}feDropShadow': self._parse_Svg_FeDropShadow, 
      '{http://www.w3.org/2000/svg}feFlood': self._parse_Svg_FeFlood, 
      '{http://www.w3.org/2000/svg}feFuncA': self._parse_Svg_FeFuncA, 
      '{http://www.w3.org/2000/svg}feFuncB': self._parse_Svg_FeFuncB, 
      '{http://www.w3.org/2000/svg}feFuncG': self._parse_Svg_FeFuncG, 
      '{http://www.w3.org/2000/svg}feFuncR': self._parse_Svg_FeFuncR, 
      '{http://www.w3.org/2000/svg}feGaussianBlur': self._parse_Svg_FeGaussianBlur, 
      '{http://www.w3.org/2000/svg}feImage': self._parse_Svg_FeImage, 
      '{http://www.w3.org/2000/svg}feMerge': self._parse_Svg_FeMerge, 
      '{http://www.w3.org/2000/svg}feMergeNode': self._parse_Svg_FeMergeNode, 
      '{http://www.w3.org/2000/svg}feMorphology': self._parse_Svg_FeMorphology, 
      '{http://www.w3.org/2000/svg}feOffset': self._parse_Svg_FeOffset, 
      '{http://www.w3.org/2000/svg}fePointLight': self._parse_Svg_FePointLight, 
      '{http://www.w3.org/2000/svg}feSpecularLighting': self._parse_Svg_FeSpecularLighting, 
      '{http://www.w3.org/2000/svg}feSpotLight': self._parse_Svg_FeSpotLight, 
      '{http://www.w3.org/2000/svg}feTile': self._parse_Svg_FeTile, 
      '{http://www.w3.org/2000/svg}feTurbulence': self._parse_Svg_FeTurbulence, 
      '{http://www.w3.org/2000/svg}filter': self._parse_Svg_Filter, 
      '{http://www.w3.org/2000/svg}foreignObject': self._parse_Svg_ForeignObject, 
      '{http://www.w3.org/2000/svg}g': self._parse_Svg_G, 
      '{http://www.w3.org/2000/svg}hatch': self._parse_Svg_Hatch, 
      '{http://www.w3.org/2000/svg}hatchpath': self._parse_Svg_Hatchpath, 
      '{http://www.w3.org/2000/svg}image': self._parse_Svg_Image, 
      '{http://www.w3.org/2000/svg}line': self._parse_Svg_Line, 
      '{http://www.w3.org/2000/svg}linearGradient': self._parse_Svg_LinearGradient, 
      '{http://www.w3.org/2000/svg}marker': self._parse_Svg_Marker, 
      '{http://www.w3.org/2000/svg}mask': self._parse_Svg_Mask, 
      '{http://www.w3.org/2000/svg}mesh': self._parse_Svg_Mesh, 
      '{http://www.w3.org/2000/svg}meshgradient': self._parse_Svg_Meshgradient, 
      '{http://www.w3.org/2000/svg}meshpatch': self._parse_Svg_Meshpatch, 
      '{http://www.w3.org/2000/svg}meshrow': self._parse_Svg_Meshrow, 
      '{http://www.w3.org/2000/svg}metadata': self._parse_Svg_Metadata, 
      '{http://www.w3.org/2000/svg}mpath': self._parse_Svg_Mpath, 
      '{http://www.w3.org/2000/svg}path': self._parse_Svg_Path, 
      '{http://www.w3.org/2000/svg}pattern': self._parse_Svg_Pattern, 
      '{http://www.w3.org/2000/svg}polygon': self._parse_Svg_Polygon, 
      '{http://www.w3.org/2000/svg}polyline': self._parse_Svg_Polyline, 
      '{http://www.w3.org/2000/svg}radialGradient': self._parse_Svg_RadialGradient, 
      '{http://www.w3.org/2000/svg}rect': self._parse_Svg_Rect, 
      '{http://www.w3.org/2000/svg}script': self._parse_Svg_Script, 
      '{http://www.w3.org/2000/svg}set': self._parse_Svg_Set, 
      '{http://www.w3.org/2000/svg}solidcolor': self._parse_Svg_Solidcolor, 
      '{http://www.w3.org/2000/svg}stop': self._parse_Svg_Stop, 
      '{http://www.w3.org/2000/svg}style': self._parse_Svg_Style, 
      '{http://www.w3.org/2000/svg}svg': self._parse_Svg_Svg, 
      '{http://www.w3.org/2000/svg}switch': self._parse_Svg_Switch, 
      '{http://www.w3.org/2000/svg}symbol': self._parse_Svg_Symbol, 
      '{http://www.w3.org/2000/svg}text': self._parse_Svg_Text, 
      '{http://www.w3.org/2000/svg}textPath': self._parse_Svg_TextPath, 
      '{http://www.w3.org/2000/svg}title': self._parse_Svg_Title, 
      '{http://www.w3.org/2000/svg}tspan': self._parse_Svg_Tspan, 
      '{http://www.w3.org/2000/svg}unknown': self._parse_Svg_Unknown, 
      '{http://www.w3.org/2000/svg}use': self._parse_Svg_Use, 
      '{http://www.w3.org/2000/svg}view': self._parse_Svg_View, 
      '{http://www.w3.org/1998/Math/MathML}math': self._parse_MathML_Math, 
      '{http://www.w3.org/1998/Math/MathML}maction': self._parse_MathML_Maction, 
      '{http://www.w3.org/1998/Math/MathML}maligngroup': self._parse_MathML_Maligngroup, 
      '{http://www.w3.org/1998/Math/MathML}malignmark': self._parse_MathML_Malignmark, 
      '{http://www.w3.org/1998/Math/MathML}menclose': self._parse_MathML_Menclose, 
      '{http://www.w3.org/1998/Math/MathML}merror': self._parse_MathML_Merror, 
      '{http://www.w3.org/1998/Math/MathML}mfenced': self._parse_MathML_Mfenced, 
      '{http://www.w3.org/1998/Math/MathML}mfrac': self._parse_MathML_Mfrac, 
      '{http://www.w3.org/1998/Math/MathML}mglyph': self._parse_MathML_Mglyph, 
      '{http://www.w3.org/1998/Math/MathML}mi': self._parse_MathML_Mi, 
      '{http://www.w3.org/1998/Math/MathML}mlabeledtr': self._parse_MathML_Mlabeledtr, 
      '{http://www.w3.org/1998/Math/MathML}mlongdiv': self._parse_MathML_Mlongdiv, 
      '{http://www.w3.org/1998/Math/MathML}mmultiscripts': self._parse_MathML_Mmultiscripts, 
      '{http://www.w3.org/1998/Math/MathML}mn': self._parse_MathML_Mn, 
      '{http://www.w3.org/1998/Math/MathML}mo': self._parse_MathML_Mo, 
      '{http://www.w3.org/1998/Math/MathML}mover': self._parse_MathML_Mover, 
      '{http://www.w3.org/1998/Math/MathML}mpadded': self._parse_MathML_Mpadded, 
      '{http://www.w3.org/1998/Math/MathML}mphantom': self._parse_MathML_Mphantom, 
      '{http://www.w3.org/1998/Math/MathML}mroot': self._parse_MathML_Mroot, 
      '{http://www.w3.org/1998/Math/MathML}mrow': self._parse_MathML_Mrow, 
      '{http://www.w3.org/1998/Math/MathML}ms': self._parse_MathML_Ms, 
      '{http://www.w3.org/1998/Math/MathML}mscarries': self._parse_MathML_Mscarries, 
      '{http://www.w3.org/1998/Math/MathML}mscarry': self._parse_MathML_Mscarry, 
      '{http://www.w3.org/1998/Math/MathML}msgroup': self._parse_MathML_Msgroup, 
      '{http://www.w3.org/1998/Math/MathML}msline': self._parse_MathML_Msline, 
      '{http://www.w3.org/1998/Math/MathML}mspace': self._parse_MathML_Mspace, 
      '{http://www.w3.org/1998/Math/MathML}msqrt': self._parse_MathML_Msqrt, 
      '{http://www.w3.org/1998/Math/MathML}msrow': self._parse_MathML_Msrow, 
      '{http://www.w3.org/1998/Math/MathML}mstack': self._parse_MathML_Mstack, 
      '{http://www.w3.org/1998/Math/MathML}mstyle': self._parse_MathML_Mstyle, 
      '{http://www.w3.org/1998/Math/MathML}msub': self._parse_MathML_Msub, 
      '{http://www.w3.org/1998/Math/MathML}msup': self._parse_MathML_Msup, 
      '{http://www.w3.org/1998/Math/MathML}msubsup': self._parse_MathML_Msubsup, 
      '{http://www.w3.org/1998/Math/MathML}mtable': self._parse_MathML_Mtable, 
      '{http://www.w3.org/1998/Math/MathML}mtd': self._parse_MathML_Mtd, 
      '{http://www.w3.org/1998/Math/MathML}mtext': self._parse_MathML_Mtext, 
      '{http://www.w3.org/1998/Math/MathML}mtr': self._parse_MathML_Mtr, 
      '{http://www.w3.org/1998/Math/MathML}munder': self._parse_MathML_Munder, 
      '{http://www.w3.org/1998/Math/MathML}munderover': self._parse_MathML_Munderover, 
      '{http://www.w3.org/1998/Math/MathML}semantics': self._parse_MathML_Semantics, 
      '{http://www.w3.org/1998/Math/MathML}annotation': self._parse_MathML_Annotation, 
      '{http://www.w3.org/1998/Math/MathML}annotation-xml': self._parse_MathML_Annotationxml, 
      '{http://www.w3.org/2000/xmlns}XML_DECL': self._parse_Xmlns_XML_DECL, 
    }
  #[[[end]]]

  def ns_uri_to_prefix(self, name):
    for key in self.namespace_map_.keys():
      search_key = '{' + self.namespace_map_[key] + '}'
      name = name.replace(search_key, key + ':')
    return name

  def parse(self, data):
    # NOTE: html5lib lowercases tokens in the scanner
    #       so the case of XML tags in SVG elements
    #       is not preserved.
    #self.tree_ = html5lib.parse(data)
    # NOTE: html5-parser strips XML namespace attributes on tags
    #self.tree_ = html5_parser.parse(data, namespace_elements=True, treebuilder="etree", maybe_xhtml=True)
    etree_parser = ETreeHTMLParser()
    etree_parser.feed(data)
    self.tree_ = etree_parser.getFragment()
    self.namespace_map_ = etree_parser.namespace_uri_map()

    astnode = None
    if isinstance(self.tree_, xml.etree.ElementTree.Element):
      astnode = self.parse_tree(self.tree_)
    elif isinstance(self.tree_, xml.etree.ElementTree.ElementTree):
      astnode = self.parse_tree(self.tree_.getroot())
    else:
      pass
    return astnode

  def parse_tree(self, root):
    astnode = parsers.ast.Node()
    for node in list(root):
      # Update namespace map
      if node.tag == xml.etree.ElementTree.Comment:
        node_tag = '{http://www.w3.org/1999/xhtml}comment'
      else:
        node_tag = node.tag
      method = self.parser_methods.get(node_tag)
      if method is not None:
        astchild = method(node)
        if astchild is not None:
          astnode.add_child(astchild)
      else:
        pass
    return astnode

  def _parse_node(self, node, astnode):
    if node.tag != astnode.tag:
      if node.tag == '{http://www.w3.org/1999/xhtml}{http://www.w3.org/2000/svg}svg':
        pass
      elif node.tag == xml.etree.ElementTree.Comment and '{http://www.w3.org/1999/xhtml}comment' == _xhtmlns(astnode.name):
        pass
      elif node.tag.lower() == astnode.tag:
        pass
      else:
        if node.tag.startswith('{http://www.w3.org/1999/xhtml}{'):
          node_tag = node.tag[len('{http://www.w3.org/1999/xhtml}'):]
        else:
          node_tag = node.tag
        if node_tag != astnode.tag:
          raise TypeError("%s passed but expecting %s" % (astnode.tag, node_tag,))
    astnode.text = node.text
    astnode.tail = node.tail

    for key in node.attrib.keys():
      attr_value = node.attrib.get(key)
      attr_key = self.ns_uri_to_prefix(key)
      astnode.set_attribute(attr_key, attr_value)
    for child in list(node):
      method = self.parser_methods.get(child.tag)
      if method is not None:
        astchild = method(child)
        if astchild is not None:
          astnode.add_child(astchild)
      else:
        if child.tag == xml.etree.ElementTree.Comment:
          method = self.parser_methods.get('{http://www.w3.org/1999/xhtml}comment')
          if method is not None:
            astchild = method(child)
            if astchild is not None:
              astnode.add_child(astchild)
          else:
            raise ValueError("no method for %s" % (child.tag,))
        else:
          astchild = parsers.ast.Node()
          astchild.name = child.tag.split('}')[-1]
          astchild.namespace = child.tag.split('}')[-2][1:]
          astchild = self._parse_node(child, astchild)
          if astchild is not None:
            astnode.add_child(astchild)
    return astnode

  '''[[[cog
  upperFirst = lambda s: s[:1].upper() + s[1:] if s else ''
  namespace = XHTML_NS
  for tag in xhtml_tags:
    node_ns   = upperFirst(namespace.split('/')[-1])
    node_name = upperFirst(tag.replace('-', ''))
    cog.outl("""  def _parse_%s_%s(self, node):
      astnode = parsers.ast.%s%sNode()
      return self._parse_node(node, astnode)
    """ % (node_ns, node_name, node_ns, node_name))
  namespace = SVG_NS
  for tag in svg_tags:
    node_ns   = upperFirst(namespace.split('/')[-1])
    node_name = upperFirst(tag.replace('-', ''))
    cog.outl("""  def _parse_%s_%s(self, node):
      astnode = parsers.ast.%s%sNode()
      return self._parse_node(node, astnode)
    """ % (node_ns, node_name, node_ns, node_name))
  namespace = MATHML_NS
  for tag in mathml_tags:
    node_ns   = upperFirst(namespace.split('/')[-1])
    node_name = upperFirst(tag.replace('-', ''))
    cog.outl("""  def _parse_%s_%s(self, node):
      astnode = parsers.ast.%s%sNode()
      return self._parse_node(node, astnode)
    """ % (node_ns, node_name, node_ns, node_name))
  namespace = XML_NS
  for tag in xml_tags:
    node_ns   = upperFirst(namespace.split('/')[-1])
    node_name = upperFirst(tag.replace('-', ''))
    cog.outl("""  def _parse_%s_%s(self, node):
      astnode = parsers.ast.%s%sNode()
      return self._parse_node(node, astnode)
    """ % (node_ns, node_name, node_ns, node_name))
  ]]]'''
  def _parse_Xhtml_Comment(self, node):
    astnode = parsers.ast.XhtmlCommentNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Html(self, node):
    astnode = parsers.ast.XhtmlHtmlNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Base(self, node):
    astnode = parsers.ast.XhtmlBaseNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Head(self, node):
    astnode = parsers.ast.XhtmlHeadNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Link(self, node):
    astnode = parsers.ast.XhtmlLinkNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Meta(self, node):
    astnode = parsers.ast.XhtmlMetaNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Style(self, node):
    astnode = parsers.ast.XhtmlStyleNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Title(self, node):
    astnode = parsers.ast.XhtmlTitleNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Body(self, node):
    astnode = parsers.ast.XhtmlBodyNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Address(self, node):
    astnode = parsers.ast.XhtmlAddressNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Article(self, node):
    astnode = parsers.ast.XhtmlArticleNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Aside(self, node):
    astnode = parsers.ast.XhtmlAsideNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Footer(self, node):
    astnode = parsers.ast.XhtmlFooterNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Header(self, node):
    astnode = parsers.ast.XhtmlHeaderNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_H1(self, node):
    astnode = parsers.ast.XhtmlH1Node()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_H2(self, node):
    astnode = parsers.ast.XhtmlH2Node()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_H3(self, node):
    astnode = parsers.ast.XhtmlH3Node()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_H4(self, node):
    astnode = parsers.ast.XhtmlH4Node()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_H5(self, node):
    astnode = parsers.ast.XhtmlH5Node()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_H6(self, node):
    astnode = parsers.ast.XhtmlH6Node()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Hgroup(self, node):
    astnode = parsers.ast.XhtmlHgroupNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Main(self, node):
    astnode = parsers.ast.XhtmlMainNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Nav(self, node):
    astnode = parsers.ast.XhtmlNavNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Section(self, node):
    astnode = parsers.ast.XhtmlSectionNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Blockquote(self, node):
    astnode = parsers.ast.XhtmlBlockquoteNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Dd(self, node):
    astnode = parsers.ast.XhtmlDdNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Div(self, node):
    astnode = parsers.ast.XhtmlDivNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Dl(self, node):
    astnode = parsers.ast.XhtmlDlNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Dt(self, node):
    astnode = parsers.ast.XhtmlDtNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Figcaption(self, node):
    astnode = parsers.ast.XhtmlFigcaptionNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Figure(self, node):
    astnode = parsers.ast.XhtmlFigureNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Hr(self, node):
    astnode = parsers.ast.XhtmlHrNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Li(self, node):
    astnode = parsers.ast.XhtmlLiNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Ol(self, node):
    astnode = parsers.ast.XhtmlOlNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_P(self, node):
    astnode = parsers.ast.XhtmlPNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Pre(self, node):
    astnode = parsers.ast.XhtmlPreNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Ul(self, node):
    astnode = parsers.ast.XhtmlUlNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_A(self, node):
    astnode = parsers.ast.XhtmlANode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Abbr(self, node):
    astnode = parsers.ast.XhtmlAbbrNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_B(self, node):
    astnode = parsers.ast.XhtmlBNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Bdi(self, node):
    astnode = parsers.ast.XhtmlBdiNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Bdo(self, node):
    astnode = parsers.ast.XhtmlBdoNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Br(self, node):
    astnode = parsers.ast.XhtmlBrNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Cite(self, node):
    astnode = parsers.ast.XhtmlCiteNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Code(self, node):
    astnode = parsers.ast.XhtmlCodeNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Data(self, node):
    astnode = parsers.ast.XhtmlDataNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Dfn(self, node):
    astnode = parsers.ast.XhtmlDfnNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Em(self, node):
    astnode = parsers.ast.XhtmlEmNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_I(self, node):
    astnode = parsers.ast.XhtmlINode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Kbd(self, node):
    astnode = parsers.ast.XhtmlKbdNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Mark(self, node):
    astnode = parsers.ast.XhtmlMarkNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Q(self, node):
    astnode = parsers.ast.XhtmlQNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Rb(self, node):
    astnode = parsers.ast.XhtmlRbNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Rp(self, node):
    astnode = parsers.ast.XhtmlRpNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Rt(self, node):
    astnode = parsers.ast.XhtmlRtNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Rtc(self, node):
    astnode = parsers.ast.XhtmlRtcNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Ruby(self, node):
    astnode = parsers.ast.XhtmlRubyNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_S(self, node):
    astnode = parsers.ast.XhtmlSNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Samp(self, node):
    astnode = parsers.ast.XhtmlSampNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Small(self, node):
    astnode = parsers.ast.XhtmlSmallNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Span(self, node):
    astnode = parsers.ast.XhtmlSpanNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Strong(self, node):
    astnode = parsers.ast.XhtmlStrongNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Sub(self, node):
    astnode = parsers.ast.XhtmlSubNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Sup(self, node):
    astnode = parsers.ast.XhtmlSupNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Time(self, node):
    astnode = parsers.ast.XhtmlTimeNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_U(self, node):
    astnode = parsers.ast.XhtmlUNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Var(self, node):
    astnode = parsers.ast.XhtmlVarNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Wbr(self, node):
    astnode = parsers.ast.XhtmlWbrNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Area(self, node):
    astnode = parsers.ast.XhtmlAreaNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Audio(self, node):
    astnode = parsers.ast.XhtmlAudioNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Img(self, node):
    astnode = parsers.ast.XhtmlImgNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Map(self, node):
    astnode = parsers.ast.XhtmlMapNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Track(self, node):
    astnode = parsers.ast.XhtmlTrackNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Video(self, node):
    astnode = parsers.ast.XhtmlVideoNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Embed(self, node):
    astnode = parsers.ast.XhtmlEmbedNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Iframe(self, node):
    astnode = parsers.ast.XhtmlIframeNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Object(self, node):
    astnode = parsers.ast.XhtmlObjectNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Param(self, node):
    astnode = parsers.ast.XhtmlParamNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Picture(self, node):
    astnode = parsers.ast.XhtmlPictureNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Source(self, node):
    astnode = parsers.ast.XhtmlSourceNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Canvas(self, node):
    astnode = parsers.ast.XhtmlCanvasNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Noscript(self, node):
    astnode = parsers.ast.XhtmlNoscriptNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Script(self, node):
    astnode = parsers.ast.XhtmlScriptNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Del(self, node):
    astnode = parsers.ast.XhtmlDelNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Ins(self, node):
    astnode = parsers.ast.XhtmlInsNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Caption(self, node):
    astnode = parsers.ast.XhtmlCaptionNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Col(self, node):
    astnode = parsers.ast.XhtmlColNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Colgroup(self, node):
    astnode = parsers.ast.XhtmlColgroupNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Table(self, node):
    astnode = parsers.ast.XhtmlTableNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Tbody(self, node):
    astnode = parsers.ast.XhtmlTbodyNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Td(self, node):
    astnode = parsers.ast.XhtmlTdNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Tfoot(self, node):
    astnode = parsers.ast.XhtmlTfootNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Th(self, node):
    astnode = parsers.ast.XhtmlThNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Thead(self, node):
    astnode = parsers.ast.XhtmlTheadNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Tr(self, node):
    astnode = parsers.ast.XhtmlTrNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Button(self, node):
    astnode = parsers.ast.XhtmlButtonNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Datalist(self, node):
    astnode = parsers.ast.XhtmlDatalistNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Fieldset(self, node):
    astnode = parsers.ast.XhtmlFieldsetNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Form(self, node):
    astnode = parsers.ast.XhtmlFormNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Input(self, node):
    astnode = parsers.ast.XhtmlInputNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Label(self, node):
    astnode = parsers.ast.XhtmlLabelNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Legend(self, node):
    astnode = parsers.ast.XhtmlLegendNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Meter(self, node):
    astnode = parsers.ast.XhtmlMeterNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Optgroup(self, node):
    astnode = parsers.ast.XhtmlOptgroupNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Option(self, node):
    astnode = parsers.ast.XhtmlOptionNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Output(self, node):
    astnode = parsers.ast.XhtmlOutputNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Progress(self, node):
    astnode = parsers.ast.XhtmlProgressNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Select(self, node):
    astnode = parsers.ast.XhtmlSelectNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Textarea(self, node):
    astnode = parsers.ast.XhtmlTextareaNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Details(self, node):
    astnode = parsers.ast.XhtmlDetailsNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Dialog(self, node):
    astnode = parsers.ast.XhtmlDialogNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Menu(self, node):
    astnode = parsers.ast.XhtmlMenuNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Summary(self, node):
    astnode = parsers.ast.XhtmlSummaryNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Slot(self, node):
    astnode = parsers.ast.XhtmlSlotNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Template(self, node):
    astnode = parsers.ast.XhtmlTemplateNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Acronym(self, node):
    astnode = parsers.ast.XhtmlAcronymNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Applet(self, node):
    astnode = parsers.ast.XhtmlAppletNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Basefont(self, node):
    astnode = parsers.ast.XhtmlBasefontNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Bgsound(self, node):
    astnode = parsers.ast.XhtmlBgsoundNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Big(self, node):
    astnode = parsers.ast.XhtmlBigNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Blink(self, node):
    astnode = parsers.ast.XhtmlBlinkNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Center(self, node):
    astnode = parsers.ast.XhtmlCenterNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Command(self, node):
    astnode = parsers.ast.XhtmlCommandNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Content(self, node):
    astnode = parsers.ast.XhtmlContentNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Dir(self, node):
    astnode = parsers.ast.XhtmlDirNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Element(self, node):
    astnode = parsers.ast.XhtmlElementNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Font(self, node):
    astnode = parsers.ast.XhtmlFontNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Frame(self, node):
    astnode = parsers.ast.XhtmlFrameNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Frameset(self, node):
    astnode = parsers.ast.XhtmlFramesetNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Image(self, node):
    astnode = parsers.ast.XhtmlImageNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Isindex(self, node):
    astnode = parsers.ast.XhtmlIsindexNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Keygen(self, node):
    astnode = parsers.ast.XhtmlKeygenNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Listing(self, node):
    astnode = parsers.ast.XhtmlListingNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Marquee(self, node):
    astnode = parsers.ast.XhtmlMarqueeNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Menuitem(self, node):
    astnode = parsers.ast.XhtmlMenuitemNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Multicol(self, node):
    astnode = parsers.ast.XhtmlMulticolNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Nextid(self, node):
    astnode = parsers.ast.XhtmlNextidNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Nobr(self, node):
    astnode = parsers.ast.XhtmlNobrNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Noembed(self, node):
    astnode = parsers.ast.XhtmlNoembedNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Noframes(self, node):
    astnode = parsers.ast.XhtmlNoframesNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Plaintext(self, node):
    astnode = parsers.ast.XhtmlPlaintextNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Shadow(self, node):
    astnode = parsers.ast.XhtmlShadowNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Spacer(self, node):
    astnode = parsers.ast.XhtmlSpacerNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Strike(self, node):
    astnode = parsers.ast.XhtmlStrikeNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Tt(self, node):
    astnode = parsers.ast.XhtmlTtNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Xmp(self, node):
    astnode = parsers.ast.XhtmlXmpNode()
    return self._parse_node(node, astnode)

  def _parse_Xhtml_Svg(self, node):
    astnode = parsers.ast.XhtmlSvgNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_A(self, node):
    astnode = parsers.ast.SvgANode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Animate(self, node):
    astnode = parsers.ast.SvgAnimateNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_AnimateMotion(self, node):
    astnode = parsers.ast.SvgAnimateMotionNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_AnimateTransform(self, node):
    astnode = parsers.ast.SvgAnimateTransformNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Circle(self, node):
    astnode = parsers.ast.SvgCircleNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_ClipPath(self, node):
    astnode = parsers.ast.SvgClipPathNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Colorprofile(self, node):
    astnode = parsers.ast.SvgColorprofileNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Defs(self, node):
    astnode = parsers.ast.SvgDefsNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Desc(self, node):
    astnode = parsers.ast.SvgDescNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Discard(self, node):
    astnode = parsers.ast.SvgDiscardNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Ellipse(self, node):
    astnode = parsers.ast.SvgEllipseNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeBlend(self, node):
    astnode = parsers.ast.SvgFeBlendNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeColorMatrix(self, node):
    astnode = parsers.ast.SvgFeColorMatrixNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeComponentTransfer(self, node):
    astnode = parsers.ast.SvgFeComponentTransferNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeComposite(self, node):
    astnode = parsers.ast.SvgFeCompositeNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeConvolveMatrix(self, node):
    astnode = parsers.ast.SvgFeConvolveMatrixNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeDiffuseLighting(self, node):
    astnode = parsers.ast.SvgFeDiffuseLightingNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeDisplacementMap(self, node):
    astnode = parsers.ast.SvgFeDisplacementMapNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeDistantLight(self, node):
    astnode = parsers.ast.SvgFeDistantLightNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeDropShadow(self, node):
    astnode = parsers.ast.SvgFeDropShadowNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeFlood(self, node):
    astnode = parsers.ast.SvgFeFloodNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeFuncA(self, node):
    astnode = parsers.ast.SvgFeFuncANode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeFuncB(self, node):
    astnode = parsers.ast.SvgFeFuncBNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeFuncG(self, node):
    astnode = parsers.ast.SvgFeFuncGNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeFuncR(self, node):
    astnode = parsers.ast.SvgFeFuncRNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeGaussianBlur(self, node):
    astnode = parsers.ast.SvgFeGaussianBlurNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeImage(self, node):
    astnode = parsers.ast.SvgFeImageNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeMerge(self, node):
    astnode = parsers.ast.SvgFeMergeNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeMergeNode(self, node):
    astnode = parsers.ast.SvgFeMergeNodeNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeMorphology(self, node):
    astnode = parsers.ast.SvgFeMorphologyNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeOffset(self, node):
    astnode = parsers.ast.SvgFeOffsetNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FePointLight(self, node):
    astnode = parsers.ast.SvgFePointLightNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeSpecularLighting(self, node):
    astnode = parsers.ast.SvgFeSpecularLightingNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeSpotLight(self, node):
    astnode = parsers.ast.SvgFeSpotLightNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeTile(self, node):
    astnode = parsers.ast.SvgFeTileNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_FeTurbulence(self, node):
    astnode = parsers.ast.SvgFeTurbulenceNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Filter(self, node):
    astnode = parsers.ast.SvgFilterNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_ForeignObject(self, node):
    astnode = parsers.ast.SvgForeignObjectNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_G(self, node):
    astnode = parsers.ast.SvgGNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Hatch(self, node):
    astnode = parsers.ast.SvgHatchNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Hatchpath(self, node):
    astnode = parsers.ast.SvgHatchpathNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Image(self, node):
    astnode = parsers.ast.SvgImageNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Line(self, node):
    astnode = parsers.ast.SvgLineNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_LinearGradient(self, node):
    astnode = parsers.ast.SvgLinearGradientNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Marker(self, node):
    astnode = parsers.ast.SvgMarkerNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Mask(self, node):
    astnode = parsers.ast.SvgMaskNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Mesh(self, node):
    astnode = parsers.ast.SvgMeshNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Meshgradient(self, node):
    astnode = parsers.ast.SvgMeshgradientNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Meshpatch(self, node):
    astnode = parsers.ast.SvgMeshpatchNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Meshrow(self, node):
    astnode = parsers.ast.SvgMeshrowNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Metadata(self, node):
    astnode = parsers.ast.SvgMetadataNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Mpath(self, node):
    astnode = parsers.ast.SvgMpathNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Path(self, node):
    astnode = parsers.ast.SvgPathNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Pattern(self, node):
    astnode = parsers.ast.SvgPatternNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Polygon(self, node):
    astnode = parsers.ast.SvgPolygonNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Polyline(self, node):
    astnode = parsers.ast.SvgPolylineNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_RadialGradient(self, node):
    astnode = parsers.ast.SvgRadialGradientNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Rect(self, node):
    astnode = parsers.ast.SvgRectNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Script(self, node):
    astnode = parsers.ast.SvgScriptNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Set(self, node):
    astnode = parsers.ast.SvgSetNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Solidcolor(self, node):
    astnode = parsers.ast.SvgSolidcolorNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Stop(self, node):
    astnode = parsers.ast.SvgStopNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Style(self, node):
    astnode = parsers.ast.SvgStyleNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Svg(self, node):
    astnode = parsers.ast.SvgSvgNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Switch(self, node):
    astnode = parsers.ast.SvgSwitchNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Symbol(self, node):
    astnode = parsers.ast.SvgSymbolNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Text(self, node):
    astnode = parsers.ast.SvgTextNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_TextPath(self, node):
    astnode = parsers.ast.SvgTextPathNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Title(self, node):
    astnode = parsers.ast.SvgTitleNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Tspan(self, node):
    astnode = parsers.ast.SvgTspanNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Unknown(self, node):
    astnode = parsers.ast.SvgUnknownNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_Use(self, node):
    astnode = parsers.ast.SvgUseNode()
    return self._parse_node(node, astnode)

  def _parse_Svg_View(self, node):
    astnode = parsers.ast.SvgViewNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Math(self, node):
    astnode = parsers.ast.MathMLMathNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Maction(self, node):
    astnode = parsers.ast.MathMLMactionNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Maligngroup(self, node):
    astnode = parsers.ast.MathMLMaligngroupNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Malignmark(self, node):
    astnode = parsers.ast.MathMLMalignmarkNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Menclose(self, node):
    astnode = parsers.ast.MathMLMencloseNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Merror(self, node):
    astnode = parsers.ast.MathMLMerrorNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mfenced(self, node):
    astnode = parsers.ast.MathMLMfencedNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mfrac(self, node):
    astnode = parsers.ast.MathMLMfracNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mglyph(self, node):
    astnode = parsers.ast.MathMLMglyphNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mi(self, node):
    astnode = parsers.ast.MathMLMiNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mlabeledtr(self, node):
    astnode = parsers.ast.MathMLMlabeledtrNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mlongdiv(self, node):
    astnode = parsers.ast.MathMLMlongdivNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mmultiscripts(self, node):
    astnode = parsers.ast.MathMLMmultiscriptsNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mn(self, node):
    astnode = parsers.ast.MathMLMnNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mo(self, node):
    astnode = parsers.ast.MathMLMoNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mover(self, node):
    astnode = parsers.ast.MathMLMoverNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mpadded(self, node):
    astnode = parsers.ast.MathMLMpaddedNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mphantom(self, node):
    astnode = parsers.ast.MathMLMphantomNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mroot(self, node):
    astnode = parsers.ast.MathMLMrootNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mrow(self, node):
    astnode = parsers.ast.MathMLMrowNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Ms(self, node):
    astnode = parsers.ast.MathMLMsNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mscarries(self, node):
    astnode = parsers.ast.MathMLMscarriesNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mscarry(self, node):
    astnode = parsers.ast.MathMLMscarryNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Msgroup(self, node):
    astnode = parsers.ast.MathMLMsgroupNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Msline(self, node):
    astnode = parsers.ast.MathMLMslineNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mspace(self, node):
    astnode = parsers.ast.MathMLMspaceNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Msqrt(self, node):
    astnode = parsers.ast.MathMLMsqrtNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Msrow(self, node):
    astnode = parsers.ast.MathMLMsrowNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mstack(self, node):
    astnode = parsers.ast.MathMLMstackNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mstyle(self, node):
    astnode = parsers.ast.MathMLMstyleNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Msub(self, node):
    astnode = parsers.ast.MathMLMsubNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Msup(self, node):
    astnode = parsers.ast.MathMLMsupNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Msubsup(self, node):
    astnode = parsers.ast.MathMLMsubsupNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mtable(self, node):
    astnode = parsers.ast.MathMLMtableNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mtd(self, node):
    astnode = parsers.ast.MathMLMtdNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mtext(self, node):
    astnode = parsers.ast.MathMLMtextNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Mtr(self, node):
    astnode = parsers.ast.MathMLMtrNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Munder(self, node):
    astnode = parsers.ast.MathMLMunderNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Munderover(self, node):
    astnode = parsers.ast.MathMLMunderoverNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Semantics(self, node):
    astnode = parsers.ast.MathMLSemanticsNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Annotation(self, node):
    astnode = parsers.ast.MathMLAnnotationNode()
    return self._parse_node(node, astnode)

  def _parse_MathML_Annotationxml(self, node):
    astnode = parsers.ast.MathMLAnnotationxmlNode()
    return self._parse_node(node, astnode)

  def _parse_Xmlns_XML_DECL(self, node):
    astnode = parsers.ast.XmlnsXML_DECLNode()
    return self._parse_node(node, astnode)

  #[[[end]]]
