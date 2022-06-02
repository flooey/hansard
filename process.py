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
    tokens = tokenize(text, data, date)
    for word in tokens:
      if word not in data or data[word].date > date:
        data[word] = WordData(word=word, date=date, snippet=tokens[word])
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
  words = set(NON_WORDS.split(lowertext))
  result = {}
  for w in words:
    if w in data and data[w].date <= date:
      continue
    m = re.search(f"(^|{NON_WORD_CHAR})({w})({NON_WORD_CHAR}|$)", lowertext)
    if not m:
      raise Exception(f'WTF? {w} ||| {text}')
    start = find_snip_boundary(lowertext, m.start(2), -1)
    end = find_snip_boundary(lowertext, m.end(2)-1, 1)
    snippet = text[start+1:end].strip()
    if end < len(text) and text[end] == '.':
      snippet += '.'
    result[w] = snippet
  return result

def find_snip_boundary(lowertext, index, dir):
  while 0 <= (index + dir) < len(lowertext):
    index += dir
    c = lowertext[index]
    if 'a' <= c <= 'z' or '0' <= c <= '9' or c in ":; ',-()":
      continue
    if c == '.':
      if index >= 2 and lowertext[index-2] == ' ' and 'a' <= lowertext[index-1] <= 'z':
        continue
      if index >= 2 and lowertext[index-2:index] == 'mr':
        continue
      if index >= 3 and (lowertext[index-3:index] == 'hon' or lowertext[index-3:index] == 'esq'):
        continue
    break
  return index

def is_snip_okay(lowertext, index):
  if index < 0 or len(lowertext) <= index:
    return False
  c = lowertext[index]
  if 'a' <= c <= 'z' or '0' <= c <= '9' or c in ":; ',-":
    return True
  if c == '.':
    if index >= 2 and lowertext[index-2] == ' ' and 'a' <= lowertext[index-1] <= 'z':
      return True
    if index >= 2 and lowertext[index-2:index] == 'mr':
      return True
    if index >= 3 and lowertext[index-3:index] == 'hon':
      return True
  return False

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