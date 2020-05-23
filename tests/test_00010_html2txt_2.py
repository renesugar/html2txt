import pytest
from html2txt import converters

# example: 10
# section: html2txt
def test_2_00010():
  html = """<abbr title="Hyper Text Markup Language">HTML</abbr>
"""
  expected_markdown = """
*[HTML]: Hyper Text Markup Language

Hyper Text Markup Language
"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
