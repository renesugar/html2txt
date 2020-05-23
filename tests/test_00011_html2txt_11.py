import pytest
from html2txt import converters

# example: 11
# section: html2txt
def test_11_00011():
  html = """<div class="bd-example" data-example-id="">
  <dl class="row">
    <dt class="col-sm-3">Description lists</dt>
    <dd class="col-sm-9">A description list is perfect for defining terms.</dd>

    <dt class="col-sm-3">Euismod</dt>
    <dd class="col-sm-9">Vestibulum id ligula porta felis euismod semper eget lacinia odio sem nec elit.</dd>
    <dd class="col-sm-9 offset-sm-3">Donec id elit non mi porta gravida at eget metus.</dd>

    <dt class="col-sm-3">Malesuada porta</dt>
    <dd class="col-sm-9">Etiam porta sem malesuada magna mollis euismod.</dd>

    <dt class="col-sm-3 text-truncate">Truncated term is truncated</dt>
    <dd class="col-sm-9">Fusce dapibus, tellus ac cursus commodo, tortor mauris condimentum nibh, ut fermentum massa justo sit amet risus.</dd>

    <dt class="col-sm-3">Nesting</dt>
    <dd class="col-sm-9">
      <dl class="row">
        <dt class="col-sm-4">Nested definition list</dt>
        <dd class="col-sm-8">Aenean posuere, tortor sed cursus feugiat, nunc augue blandit nunc.</dd>
      </dl>
    </dd>
  </dl>
</div>

"""
  expected_markdown = """
  
  Description lists
: A description list is perfect for defining terms.
Euismod
: Vestibulum id ligula porta felis euismod semper eget lacinia odio sem nec elit.
: Donec id elit non mi porta gravida at eget metus.
Malesuada porta
: Etiam porta sem malesuada magna mollis euismod.
Truncated term is truncated
: Fusce dapibus, tellus ac cursus commodo, tortor mauris condimentum nibh, ut fermentum massa justo sit amet risus.
Nesting
:     Nested definition list
    : Aenean posuere, tortor sed cursus feugiat, nunc augue blandit nunc.

    


  

"""
  markdown = converters.Html2Markdown().convert(html)
  assert markdown == expected_markdown
