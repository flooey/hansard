#!/usr/bin/env python3

from collections import namedtuple
import itertools
import re
import sys
import xml.etree.ElementTree as ET

WordData = namedtuple('WordData', ['word', 'date', 'snippet'])

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
  date = house.find('date').attrib['format']
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

NON_WORDS = re.compile(r"[^\w'-]+")

def tokenize(text, data, date):
  lowertext = text.casefold()
  words = set(NON_WORDS.split(lowertext))
  result = {}
  for w in words:
    if w in data and data[w].date <= date:
      continue
    m = re.search(f"(^|[^\\w'-])({w})([^\\w'-]|$)", lowertext)
    if not m:
      raise Exception(f'WTF? {w} ||| {text}')
    start = m.start(2)
    while is_snip_okay(lowertext, start):
      start -= 1
    end = m.end(2)
    while is_snip_okay(lowertext, end):
      end += 1
    snippet = text[start+1:end].strip()
    if end < len(text) and text[end] == '.':
      snippet += '.'
    result[w] = snippet
  return result

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
  data = {}
  for f in sys.argv[1:]:
    words_for_file(f, data)
  print(len(data))

if __name__ == '__main__':
  main()