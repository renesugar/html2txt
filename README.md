# html2txt

html2txt converts HTML to markdown.

# Usage

Import the module.

```python
from html2txt import converters
```

Call the **Html2Markdown** converter on HTML text to convert it to markdown.

```python
markdown = converters.Html2Markdown().convert(html)
```

# Run converter for unit testing

```bash
> cd html2txt/converters
> python3 -B html2markdown.py --path path-to-html-directory
```

# Tests

## Create Virtual Environment

```bash
> cd html2txt

> python3 -m venv venv

> source ./venv/bin/activate
```

## Making Tests

The [Commonmark](https://commonmark.org/) and [Breakdance](https://breakdance.github.io/breakdance/) tests were written for converting markdown to HTML so many tests fail with differences of whitespace and choices of markdown representation.

Breakdance is used by [Dillinger](https://dillinger.io/), a markdown editor.

```bash
> cd html2txt/tests

> python3 -B ./config/mkhtml2txt.py --path .

> python3 -B ./config/mkcommonmark.py --path .

> python3 -B ./config/mkbreakdance.py --path .

> python3 -B ./config/mksvgweb.py --path .

> python3 -B ./config/mkmathml.py --path .
```

## Running Tests

```bash
> pytest -vv
```