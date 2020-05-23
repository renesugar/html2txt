import re
import os
import argparse
import sys
import errno
import optparse
import uuid
import json

#
# MIT License
#
# https://opensource.org/licenses/MIT
#
# Copyright 2020 Rene Sugar
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#
# Description:
#
# This program reads JSON files to create pytest tests.
#

def checkExtension(file, exts):
  name, extension = os.path.splitext(file)
  extension = extension.lstrip(".")
  processFile = 0
  if len(extension) == 0:
    processFile = 0
  elif len(exts) == 0:
    processFile = 1
  elif extension in exts:
    processFile = 1
  else:
    processFile = 0
  return processFile

def checkExclusion(dir, rootPath, excludePaths):
  processDir = 0
  if (dir[0:1] == "."):
    processDir = 0
  elif os.path.join(rootPath,dir) in excludePaths:
    processDir = 0
  else:
    processDir = 1
  return processDir

def filelist(dir, excludePaths, exts):
  allfiles = []
  for path, subdirs, files in os.walk(dir):
    files = [os.path.join(path,x) for x in files if checkExtension(x, exts)]
    # "[:]" alters the list of subdirectories walked by os.walk
    # https://stackoverflow.com/questions/10620737/efficiently-removing-subdirectories-in-dirnames-from-os-walk
    subdirs[:] = [os.path.join(path,x) for x in subdirs if checkExclusion(x, path, excludePaths)]
    allfiles.extend(files)
    for x in subdirs:
      allfiles.extend(filelist(x, excludePaths, exts))
  return allfiles

def main():
  parser = argparse.ArgumentParser(description="mdtext")
  parser.add_argument("--path", help="Base path of the project to be scanned", default=".")
  parser.add_argument("--root", help="Root path of the project to be scanned", default="/")
  parser.add_argument("--prefix", help="Replace root path with this prefix", default="/")
  parser.add_argument("--extensions", help="File extensions that are processed", default=".json")
  parser.add_argument("--exclude", nargs='*', help="Paths of folders to exclude", default=[])

  args = vars(parser.parse_args())

  basePath = os.path.abspath(os.path.expanduser(args['path']))

  rootPath = args['root']

  rootPrefix = args['prefix']

  fileExtensions = args['extensions'].lstrip(".").split(".")

  excludePaths = args['exclude']

  # Remove trailing path separator from each exclude path
  excludePaths[:] = [x.rstrip(os.sep) for x in excludePaths]

  commonmarkPath = os.path.join(basePath, 'commonmark')

  files = filelist(commonmarkPath, excludePaths, fileExtensions)

  # Read each file
  for file in files:
    file_canonical = file.replace(rootPath, rootPrefix, 1)

    filePath, fileName = os.path.split(file_canonical)
    baseName, fileExt  = os.path.splitext(fileName)

    baseName = baseName.replace('-', '_')

    with open(file, 'r') as f:
      tests = json.load(f)

      # {
      #   "markdown": "\tfoo\tbaz\t\tbim\n",
      #   "html": "<pre><code>foo\tbaz\t\tbim\n</code></pre>\n",
      #   "example": 1,
      #   "start_line": 355,
      #   "end_line": 360,
      #   "section": "Tabs"
      # },

      i = 0
      for test in tests:
        i += 1
        expected_markdown = test['markdown']
        html = test['html']
        example = int(test['example'])
        start_line = int(test['start_line'])
        end_line = int(test['end_line'])
        section = test['section']

        # Replace "_" with "*" in expected_markdown if not found in HTML
        # as tests were written for testing markdown to HTML
        if html.find('_') == -1:
          expected_markdown = expected_markdown.replace('_', '*')

        testfile = f'test_{i:05}_' + baseName + ".py"

        outputFile = os.path.join(basePath, testfile)

        with open(outputFile, 'w') as o:
          o.write(f"import pytest\n")
          o.write(f"from html2txt import converters\n\n")
          o.write(f"# example: {example}\n")
          o.write(f"# start_line: {start_line}\n")
          o.write(f"# end_line: {end_line}\n")
          o.write(f"# section: {section}\n")
          o.write(f"def test_{baseName}_{i:05}():\n")
          o.write(f"  html = \"\"\"{html}\"\"\"\n")
          o.write(f"  expected_markdown = \"\"\"{expected_markdown}\"\"\"\n")
          o.write(f"  markdown = converters.Html2Markdown().convert(html)\n")
          o.write(f"  assert markdown == expected_markdown\n")

if __name__ == "__main__":
  main()

