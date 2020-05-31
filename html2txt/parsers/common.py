import os
import sys

from xml.sax.saxutils import escape, quoteattr
import html

import urllib
from urllib.parse import urlparse
from urllib.parse import unquote
from urllib.parse import quote

import re

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

def escape_url(link):
  if link is None:
    link = ""
  # () are not safe in a markdown URL
  safe = '/#:*?=%@+,&'
  return html.escape(quote(html.unescape(link), safe=safe))

def escape_html(s):
  if s is None:
    s = ""
  return html.escape(html.unescape(s)).replace('&#x27;', "'")
