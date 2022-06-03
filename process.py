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
    date, text = text_for_house(node, os.path.basename(filename))
    tokenize(text, data, date, os.path.basename(filename), node.tag[5:])
  return data

DATE_FIXES = {
  ('0982-11-16', 'S6CV0032P0.xml'): '1982-11-16',
  ('1013-06-24', 'S5LV0014P0.xml'): '1913-06-24',
  ('1054-04-07', 'S5LV0186P0.xml'): '1954-04-07',
  ('1093-03-09', 'S6CV0038P0.xml'): '1983-03-09',
  ('1101-08-10', 'S5CV0029P0.xml'): '1911-08-10',
  ('1643-05-18', 'S5CV0389P0.xml'): '1943-05-18',
  ('1802-07-02', 'S1V0005P0.xml'): '1805-07-02',
  ('1803-03-29', 'S1V0001P0.xml'): '1804-03-29',
  ('1804-04-09', 'S4V0022P0.xml'): '1894-04-09',
  ('1804-05-03', 'S4V0024P0.xml'): '1894-05-03',
  ('1805-04-02', 'S1V0006P0.xml'): '1806-04-02',
  ('1806-01-03', 'S1V0008P0.xml'): '1807-01-03',
  ('1806-01-17', 'S1V0008P0.xml'): '1807-01-16',
  ('1809-03-13', 'S1V0006P0.xml'): '1806-03-13',
  ('1809-03-13', 'S1V0009P0_a.xml'): '1807-03-13',
  ('1809-03-17', 'S1V0009P0_a.xml'): '1807-03-17',
  ('1809-07-01', 'S1V0009P0_b.xml'): '1807-07-01',
  ('1837-01-16', 'S3V0040P0.xml'): '1838-01-16',
  ('1846-01-26', 'S3V0089P0.xml'): '1847-01-26',
  ('1868-02-24', 'S3V0194P0.xml'): '1869-02-24',
  ('1898-08-03', 'S4V0015P0.xml'): '1893-08-03',
  ('1900-12-11', 'S6CV0182P0.xml'): '1990-12-11',
  ('1907-03-23', 'S1V0009P0_a.xml'): '1807-03-23',
  ('1925-05-03', 'S2V0013P0.xml'): '1825-05-03',
  ('19389-02-23', 'S5LV0111P0.xml'): '1938-02-23',
  ('1974-04-14', 'S6CV0241P0.xml'): '1994-04-14',
  ('1983-04-20', 'S4V0011P0.xml'): '1893-04-20',
  ('1983-05-09', 'S4V0012P0.xml'): '1893-05-09',
  ('1993-05-16', 'S4V0012P0.xml'): '1893-05-16',
  ('19940-02-16', 'S5LV0552P0.xml'): '1994-02-16',
  ('19954-06-27', 'S5LV0565P0.xml'): '1995-06-27',
  ('2001-11-19', 'S6CV0129P0.xml'): '1988-03-07',
}

def text_for_house(house, filename):
  date = house.find('date').attrib['format'].strip()
  if (date, filename) in DATE_FIXES:
    date = DATE_FIXES[(date, filename)]
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
        if snip_end < len(text) and text[snip_end] in ".?!":
          snippet += text[snip_end]
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

ALLOWED_ABBREVIATIONS = ['mr', 'mrs', 'ms', 'hon', 'esq', 'no', 'nos', '&c']

def find_snip_boundary(lowertext, index, dir):
  keep_going = True
  while 0 <= index < len(lowertext) and keep_going:
    keep_going = False
    c = lowertext[index]
    if c.isalpha() or '0' <= c <= '9' or c in ":; ',-()&":
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