import pytest
from html2txt import converters

# example: 7
# section: html2txt
def test_3_00007():
  html = """<blockquote>
<pre><code>  foo
</code></pre>
</blockquote>
"""
  expected_markdown = """>
><pre>
>
>```
>  foo
>
>```
>
></pre>
>
>
"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
