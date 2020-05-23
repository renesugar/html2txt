import pytest
from html2txt import converters

# example: 12
# section: html2txt
def test_1_00012():
  html = """<p>Foo <responsive-image src="foo.jpg" /></p>
"""
  expected_markdown = """Foo<responsive-image src="foo.jpg"/>

"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
