#!/usr/bin/env python3

import argparse
from collections import namedtuple
import itertools
import json
import re
import sys
import xml.etree.ElementTree as ET

WordData = namedtuple('WordData', ['word', 'date', 'snippet'])

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def words_for_file(filename, data={}):
  tree = ET.parse(open(filename))
  root = tree.getroot()
  for node in itertools.chain(root.findall('housecommons'), root.findall('houselords')):
    date, text = text_for_house(node)
    tokenize(text, data, date)
  return data

def text_for_house(house):
  date = house.find('date').attrib['format'].strip()
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

def tokenize(text, data, date):
  lowertext = text.casefold()
  index = 0
  while index < len(lowertext):
    if lowertext[index].isalpha():
      start, index = make_word(lowertext, index)
      word = lowertext[start:index]
      if word not in data or data[word].date > date:
        snip_start = find_snip_boundary(lowertext, start, -1)
        snip_end = find_snip_boundary(lowertext, index-1, 1)
        snippet = text[snip_start+1:snip_end].strip()
        if snip_end < len(text) and text[snip_end] == '.':
          snippet += '.'
        data[word] = WordData(word, date, snippet)
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

def find_snip_boundary(lowertext, index, dir):
  while 0 <= (index + dir) < len(lowertext):
    index += dir
    c = lowertext[index]
    if c.isalpha() or '0' <= c <= '9' or c in ":; ',-()":
      continue
    if c == '.':
      if index >= 2 and lowertext[index-2] == ' ' and lowertext[index-1].isalpha():
        continue
      if index >= 2 and lowertext[index-2:index] == 'mr':
        continue
      if index >= 3 and (lowertext[index-3:index] == 'hon' or lowertext[index-3:index] == 'esq'):
        continue
    break
  return index

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