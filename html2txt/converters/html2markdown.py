import os
import sys
import argparse

from  html2txt import parsers

#from importlib import reload # reload 
#reload(parsers)


#!/usr/bin/env python3
# Copyright (c) 2020 Rene Sugar.
# License: MIT (http://www.opensource.org/licenses/mit-license.php)

class Html2Markdown(object):
  def __init(self):
    self.root_ = None

  def convert(self, data):
    p = parsers.HtmlParser()
    self.root_ = p.parse(data)
    m = parsers.MarkdownVisitor()
    m.visit(self.root_)
    return m.text

  @property
  def root(self):
    return self.root_

def html_to_markdown(data):
  hmd = Html2Markdown()
  return hmd.convert(data)

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
  parser.add_argument("--extensions", help="File extensions that are processed", default=".html.svg")
  parser.add_argument("--exclude", nargs='*', help="Paths of folders to exclude", default=[])

  args = vars(parser.parse_args())

  basePath = os.path.abspath(os.path.expanduser(args['path']))

  rootPath = args['root']

  rootPrefix = args['prefix']

  fileExtensions = args['extensions'].lstrip(".").split(".")

  excludePaths = args['exclude']

  # Remove trailing path separator from each exclude path
  excludePaths[:] = [x.rstrip(os.sep) for x in excludePaths]

  files = filelist(basePath, excludePaths, fileExtensions)

  # Read each file
  for file in files:
    file_canonical = file.replace(rootPath, rootPrefix, 1)

    print("file = %s" % (file_canonical,))

    with open(file, 'r') as f:
      lines = f.readlines()

      data = ''.join(lines)

      md = html_to_markdown(data)

      print(md)

if __name__ == "__main__":
  main()
