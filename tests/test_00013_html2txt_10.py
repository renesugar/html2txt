import pytest
from html2txt import converters

# example: 13
# section: html2txt
def test_10_00013():
  html = """<!DOCTYPE html>
<html>
  <head>
    <title>Sample document 3</title>
    <link rel="stylesheet" href="style3.css">
  </head>
  <body>
    <table id="demo-table">
      <caption>Oceans</caption>
      <thead>
        <tr>
          <th></th>
          <th>Area</th>
          <th>Mean depth</th>
        </tr>
        <tr>
          <th></th>
          <th>million km<sup>2</sup></th>
          <th>m</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Arctic</th>
          <td>13,000</td>
          <td>1,200</td>
        </tr>
        <tr>
          <th>Atlantic</th>
          <td>87,000</td>
          <td>3,900</td>
        </tr>
        <tr>
          <th>Pacific</th>
          <td>180,000</td>
          <td>4,000</td>
        </tr>
        <tr>
          <th>Indian</th>
          <td>75,000</td>
          <td>3,900</td>
        </tr>
        <tr>
          <th>Southern</th>
          <td>20,000</td>
          <td>4,500</td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <th>Total</th>
          <td>361,000</td>
          <td></td>
        </tr>
        <tr>
          <th>Mean</th>
          <td>72,000</td>
          <td>3,800</td>
        </tr>
      </tfoot>
    </table>
  </body>
</html>
"""
  expected_markdown = """
  
    % Sample document 3


    
  
    
<caption>Oceans</caption>
  
||Area<br>million km<sup>2</sup>|Mean depth<br>m|
|---|---|---|
|Arctic|13,000|1,200|
|Atlantic|87,000|3,900|
|Pacific|180,000|4,000|
|Indian|75,000|3,900|
|Southern|20,000|4,500|
|Total|361,000||
|Mean|72,000|3,800|


  

"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
