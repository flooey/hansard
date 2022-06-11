#!/usr/bin/env python3

from process import date_it
import argparse
from datetime import date, timedelta
import os.path
import sys
import xml.etree.ElementTree as ET

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

ALLOWABLE_GAP = timedelta(days=150)

def check_file(filename):
  tree = ET.parse(open(filename))
  root = tree.getroot()
  dates = []
  for node in root.iter('date'):
    date_string = date_it(node, os.path.basename(filename))
    d = date.fromisoformat(date_string)
    if len(dates) > 0 and (d - dates[-1] > ALLOWABLE_GAP or dates[-1] - d > ALLOWABLE_GAP):
      print(f"  {dates[-1]} -> {d} [{node.text}] - (first date {dates[0]})")
      print(f"  ('{d}', '{os.path.basename(filename)}'): '{d}',")
      print()
    dates.append(d)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('files', nargs='+')
  args = parser.parse_args()
  for f in args.files:
    eprint(f)
    check_file(f)

if __name__ == '__main__':
  main()