import os
import sys
import re

from setuptools import find_namespace_packages
from setuptools import find_packages
from setuptools import setup

with open('html2txt/__init__.py', 'r') as fh:
  setup_info = fh.read()
  __version__ ,= re.findall("__version__ = '(.*)'", setup_info)
  __author__ ,= re.findall("__author__ = '(.*)'", setup_info)
  __email__ ,= re.findall("__email__ = '(.*)'", setup_info)
  setup_info = None

with open("README.md", "r") as fh:
  long_description = fh.read()

install_requires = [
  "html5lib>=1.0.1",
  "mistune==0.8.4",
  "six>=1.14.0",
  "webencodings>=0.5.1",
]

tests_require = [
  "appdirs>=1.4.4",
  "attrs>=19.3.0",
  "colorama>=0.4.3",
  "distlib>=0.3.0",
  "docopt>=0.6.2",
  "filelock>=3.0.12",
  "importlib-metadata>=1.6.0",
  "more-itertools>=8.2.0",
  "packaging>=20.3",
  "pathtools>=0.1.2",
  "pluggy>=0.13.1",
  "py>=1.8.1",
  "pyparsing>=2.4.7",
  "pytest>=5.4.1",
  "pytest-mock>=3.1.0",
  "pytest-watch>=4.2.0",
  "six>=1.14.0",
  "toml>=0.10.0",
  "tox>=3.15.0",
  "virtualenv>=20.0.20",
  "watchdog>=0.10.2",
  "wcwidth>=0.1.9",
  "zipp>=3.1.0",
]

classifiers = """\
Development Status :: 3 - Alpha
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Operating System :: OS Independent
Topic :: Software Development :: Libraries :: Python Modules
Topic :: Software Development :: Documentation
Topic :: Text Processing :: Filters
Topic :: Text Processing :: Markup :: HTML
"""

setup(
  name="html2txt",
  version=__version__,
  maintainer=__author__,
  maintainer_email=__email__,
  author=__author__,
  author_email=__email__,
  license="MIT",
  keywords = "markdown HTML converter ast",
  platforms=["any"],
  namespace_packages=['html2txt'],
  packages=find_packages(),
  requires = [],
  install_requires=install_requires,
  tests_require=tests_require,
  package_data = {'': ['*.md']},
  description="Convert HTML to markdown",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/renesugar/html2txt",
  project_urls={
      "Bug Tracker": "https://github.com/renesugar/html2txt/issues",
      "Documentation": "https://github.com/renesugar/html2txt/wiki",
      "Source Code": "https://github.com/renesugar/html2txt",
  },
  download_url = "https://github.com/renesugar/html2txt/tarball/master",
  classifiers=filter(None, classifiers.split("\n")),
  python_requires='>=3.6',
  zip_safe=False,
)
