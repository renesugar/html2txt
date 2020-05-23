import pytest
from html2txt import converters

# example: 5
# section: html2txt
def test_4_00005():
  html = """<blockquote>foo</blockquote>
"""
  expected_markdown = """"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
