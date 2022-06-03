#!/usr/bin/env python3

import argparse
from collections import namedtuple
import itertools
import json
import os.path
import re
import sys
import xml.etree.ElementTree as ET

WordData = namedtuple('WordData', ['word', 'date', 'snippet', 'house', 'file'])

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def words_for_file(filename, data={}):
  tree = ET.parse(open(filename))
  root = tree.getroot()
  for node in itertools.chain(root.findall('housecommons'), root.findall('houselords')):
    date, text = text_for_house(node)
    tokenize(text, data, date, os.path.basename(filename), node.tag[5:])
  return data

DATE_FIXES = {
  '0982-11-16': '1982-11-16',  # S6CV0032P0
  '1013-06-24': '1913-06-24',  # S5LV0014P0
  '1054-04-07': '1954-04-07',  # S5LV0186P0
  '1093-03-09': '1983-03-09',  # S6CV0038P0
  '1101-08-10': '1911-08-10',  # S5CV0029P0
  '1643-05-18': '1943-05-18',  # S5CV0389P0
}

def text_for_house(house):
  date = house.find('date').attrib['format'].strip()
  if date in DATE_FIXES:
    date = DATE_FIXES[date]
  for n in house.iter('col'):
    n.text = ''
  return date, " ".join(map(text_for_holder, list(house.iter('p'))))

def text_for_holder(holder):
  text = ""
  for t in holder.itertext():
    t = t.strip()
    text += t
    if t.endswith("-"):
      text = text[:-1]
    else:
      text += " "
  return text

NON_WORD_CHAR = r"[^\w'-]"
NON_WORDS = re.compile(f"{NON_WORD_CHAR}+")

def tokenize(text, data, date, filename, house):
  lowertext = text.casefold()
  index = 0
  while index < len(lowertext):
    if lowertext[index].isalpha():
      start, index = make_word(lowertext, index)
      word = lowertext[start:index]
      if word not in data or data[word].date > date:
        snip_start = find_snip_boundary(lowertext, start, -1)
        snip_end = 1 + find_snip_boundary(lowertext, index-1, 1)
        snippet = text[snip_start:snip_end].strip()
        if snip_end < len(text) and text[snip_end] == '.':
          snippet += '.'
        data[word] = WordData(word, date, snippet, house, filename)
    index += 1

def make_word(lowertext, index):
  start_index = index
  while index < len(lowertext):
    c = lowertext[index]
    if c.isalpha():
      index += 1
      continue
    if c == "'" or c == '-':
      if index + 1 < len(lowertext) and lowertext[index+1].isalpha():
        index += 1
        continue
    break
  return (start_index, index)

ALLOWED_ABBREVIATIONS = ['mr', 'mrs', 'ms', 'hon', 'esq', 'no', 'nos']

def find_snip_boundary(lowertext, index, dir):
  keep_going = True
  while 0 <= index < len(lowertext) and keep_going:
    keep_going = False
    c = lowertext[index]
    if c.isalpha() or '0' <= c <= '9' or c in ":; ',-()":
      keep_going = True
    if c == '.':
      if index >= 2 and lowertext[index-2] == ' ' and lowertext[index-1].isalpha():
        keep_going = True
      else:
        for abbr in ALLOWED_ABBREVIATIONS:
          if index >= len(abbr) and lowertext[index-len(abbr):index] == abbr:
            keep_going = True
            break
    if keep_going:
      index += dir
  return index - dir

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('files', nargs='+')
  parser.add_argument('--save', action='store_true')
  parser.add_argument('--load', action='store_true')
  args = parser.parse_args()
  data = {}
  if args.load:
    loaded = json.load(open('data.json'))
    for k in loaded:
      data[k] = WordData(*loaded[k])
  for f in args.files:
    eprint(f)
    words_for_file(f, data)
  print(len(data))
  if args.save:
    json.dump(data, open('data.json', 'w'), indent=2, sort_keys=True)

if __name__ == '__main__':
  main()