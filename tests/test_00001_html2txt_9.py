import pytest
from html2txt import converters

# example: 1
# section: html2txt
def test_9_00001():
  html = """<ul class="nav navbar-nav">
  <li class="nav-item"> Bootstrap </li>
  <li class="nav-item"> Documentation </li>
  <li class="nav-item"> Examples </li>
  <li class="nav-item"> Themes </li>
  <li class="nav-item"> Expo </li>
  <li class="nav-item"> Blog </li>
</ul>
"""
  expected_markdown = """*  Bootstrap 
*  Documentation 
*  Examples 
*  Themes 
*  Expo 
*  Blog 

"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
