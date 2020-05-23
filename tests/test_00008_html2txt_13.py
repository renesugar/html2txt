import pytest
from html2txt import converters

# example: 8
# section: html2txt
def test_13_00008():
  html = """<!-- from https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table -->
    <p>Simple table with header</p>
    <table>
      <tr>
        <th>First name</th>
        <th>Last name</th>
      </tr>
      <tr>
        <td>John</td>
        <td>Doe</td>
      </tr>
      <tr>
        <td>Jane</td>
        <td>Doe</td>
      </tr>
    </table>

"""
  expected_markdown = """[//]: # ( from https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table )
    Simple table with header

    
|First name|Last name|
|---|---|
|John|Doe|
|Jane|Doe|



"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
