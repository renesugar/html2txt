import pytest
from html2txt import converters

# example: 14
# section: html2txt
def test_7_00014():
  html = """<!--
This is a comment.
-->
<p>hello</p>
<p>there</p>
"""
  expected_markdown = """[//]: # (
This is a comment.
)
hello

there

"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
