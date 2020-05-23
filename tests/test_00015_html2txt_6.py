import pytest
from html2txt import converters

# example: 15
# section: html2txt
def test_6_00015():
  html = """<h3 id="blockquote">Blockquote</h3>

<p>The default <code class="highlighter-rouge">margin</code> on blockquotes is <code class="highlighter-rouge">1em 40px</code>, so we reset that to <code class="highlighter-rouge">0 0 1rem</code> for something more consistent with other elements.</p>

<div class="bd-example">
  <blockquote class="blockquote">
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer posuere erat a ante.</p>
    <footer>Someone famous in <cite title="Source Title">Source Title</cite></footer>
  </blockquote>
</div>
"""
  expected_markdown = """### Blockquote

The default`margin` on blockquotes is `1em 40px`, so we reset that to `0 0 1rem` for something more consistent with other elements.



  
  >Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer posuere erat a ante.
>
>    Someone famous in <cite title="Source Title">Source Title</cite>
>  

  
"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
