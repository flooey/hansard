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
    for date, text in texts_for_house(node, os.path.basename(filename)):
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
  ('1805-10-10', 'S1V0004P0.xml'): '1805-04-10',
  ('1806-01-03', 'S1V0008P0.xml'): '1807-01-03',
  ('1806-01-17', 'S1V0008P0.xml'): '1807-01-16',
  ('1807-04-05', 'S4V0048P0.xml'): '1897-04-05',
  ('1809-03-13', 'S1V0006P0.xml'): '1806-03-13',
  ('1809-03-13', 'S1V0009P0_a.xml'): '1807-03-13',
  ('1809-03-17', 'S1V0009P0_a.xml'): '1807-03-17',
  ('1809-07-01', 'S1V0009P0_b.xml'): '1807-07-01',
  ('1819-03-14', 'S1V0041P0.xml'): '1819-12-14',
  ('1827-11-05', 'S2V0017P0.xml'): '1827-05-11',
  ('1837-01-16', 'S3V0040P0.xml'): '1838-01-16',
  ('1846-01-26', 'S3V0089P0.xml'): '1847-01-26',
  ('1868-02-24', 'S3V0194P0.xml'): '1869-02-24',
  ('1890-12-18', 'S5CV0996P0.xml'): '1980-12-18',
  ('1898-08-03', 'S4V0015P0.xml'): '1893-08-03',
  ('1900-12-11', 'S6CV0182P0.xml'): '1990-12-11',
  ('1901-02-26', 'S4V0103P0.xml'): '1902-02-26',
  ('1902-03-12', 'S5LV0011P0.xml'): '1912-03-12',
  ('1906-02-16', 'S5LV0001P0.xml'): '1909-02-16',
  ('1906-03-01', 'S5CV0001P0.xml'): '1909-03-01',
  ('1906-11-22', 'S5LV0226P0.xml'): '1960-11-22',
  ('1907-03-02', 'S5LV0001P0.xml'): '1909-03-02',
  ('1907-03-23', 'S1V0009P0_a.xml'): '1807-03-23',
  ('1908-07-10', 'S5CV0988P0.xml'): '1980-07-10',
  ('1910-02-12', 'S5CV0112P0.xml'): '1919-02-12',
  ('1910-05-21', 'S5CV0116P0.xml'): '1919-05-21',
  ('1910-08-15', 'S4V0099P0.xml'): '1901-08-15',
  ('1911-08-25', 'S5LV0017P0.xml'): '1914-08-25',
  ('1912-12-04', 'S5CV0036P0.xml'): '1912-04-12',
  ('1913-11-01', 'S5CV0043P0.xml'): '1912-11-01',
  ('1913-12-12', 'S5CV0045P0.xml'): '1912-12-12',
  ('1914-03-21', 'S5LV0131P0.xml'): '1944-03-21',
  ('1917-05-15', 'S5LV0026P0.xml'): '1917-11-15',
  ('1920-07-21', 'S5CV0186P0.xml'): '1925-07-21',
  ('1924-03-17', 'S5LV0060P0.xml'): '1925-03-17',
  ('1924-03-18', 'S5LV0060P0.xml'): '1925-03-18',
  ('1925-05-03', 'S2V0013P0.xml'): '1825-05-03',
  ('1927-02-28', 'S5LV0070P0.xml'): '1928-02-28',
  ('1927-03-01', 'S5LV0070P0.xml'): '1928-03-01',
  ('1928-03-06', 'S5CV0161P0.xml'): '1923-03-06',
  ('1928-03-27', 'S5CV0162P0.xml'): '1923-03-27',
  ('1928-04-10', 'S5CV0162P0.xml'): '1923-04-10',
  ('1928-05-04', 'S5CV0163P0.xml'): '1923-05-04',
  ('1928-07-28', 'S5LV0211P0.xml'): '1958-07-28',
  ('1929-07-05', 'S5LV0075P0.xml'): '1929-12-05',
  ('1929-12-06', 'S5CV0200P0.xml'): '1926-12-06',
  ('1930-11-02', 'S5CV0134P0.xml'): '1920-11-02',
  ('1931-07-18', 'S5LV0014P0.xml'): '1913-07-18',
  ('1932-07-03', 'S5CV0156P0.xml'): '1922-07-03',
  ('1932-07-20', 'S5CV0156P0.xml'): '1922-07-20',
  ('1932-07-21', 'S5CV0156P0.xml'): '1922-07-21',
  ('1933-03-02', 'S5CV0181P0.xml'): '1925-03-02',
  ('1933-06-12', 'S5CV0283P0.xml'): '1933-12-06',
  ('1933-07-20', 'S6CV0046P0.xml'): '1983-07-20',
  ('1933-11-04', 'S5LV0087P0.xml'): '1933-04-11',
  ('1933-11-10', 'S6CV0048P0.xml'): '1983-11-10',
  ('1933-11-11', 'S6CV0048P0.xml'): '1983-11-11',
  ('1936-04-21', 'S5LV0063P0.xml'): '1926-04-21',
  ('1936-07-24', 'S5LV0075P0.xml'): '1929-07-24',
  ('1936-07-27', 'S5LV0075P0.xml'): '1929-11-27',
  ('19389-02-23', 'S5LV0111P0.xml'): '1939-02-23',
  ('1939-07-26', 'S5CV0230P0.xml'): '1929-07-26',
  ('1940-01-21', 'S5LV0118P0.xml'): '1941-01-21',
  ('1941-07-27', 'S5LV0017P0.xml'): '1914-07-27',
  ('1942-05-20', 'S5LV0057P0.xml'): '1924-05-20',
  ('1942-07-23', 'S5LV0054P0.xml'): '1923-07-23',
  ('1943-06-13', 'S5LV0092P0.xml'): '1934-06-13',
  ('1944-01-11', 'S5CV0404P0.xml'): '1944-11-01',
  ('1945-04-12', 'S5CV0416P0.xml'): '1945-12-04',
  ('1945-06-12', 'S5CV0416P0.xml'): '1945-12-06',
  ('1947-01-21', 'S5LV0153P0.xml'): '1948-01-21',
  ('1947-02-10', 'S5CV0447P0.xml'): '1948-02-10',
  ('1947-02-11', 'S5LV0153P0.xml'): '1948-02-11',
  ('1947-06-25', 'S5CV0875P0.xml'): '1974-06-25',
  ('1948-02-22', 'S5LV0160P0.xml'): '1949-02-22',
  ('1948-12-13', 'S5LV0153P0.xml'): '1948-02-13',
  ('1950-05-14', 'S4V0083P0.xml'): '1900-05-14',
  ('1953-07-21', 'S6CV0046P0.xml'): '1983-07-21',
  ('1953-12-02', 'S5LV0180P0.xml'): '1953-02-12',
  ('1953-12-25', 'S5LV0180P0.xml'): '1953-02-25',
  ('1954-02-20', 'S5CV0689P0.xml'): '1964-02-20',
  ('1954-12-08', 'S5CV0523P0.xml'): '1954-02-08',
  ('1955-11-02', 'S5CV0536P0.xml'): '1955-02-11',
  ('1956-05-29', 'S5CV0423P0.xml'): '1946-05-29',
  ('1956-10-28', 'S5LV0219P0.xml'): '1959-10-28',
  ('1957-10-31', 'S5CV0898P0.xml'): '1975-10-31',
  ('1958-12-21', 'S5CV0580P0.xml'): '1958-01-21',
  ('1958-12-22', 'S5CV0580P0.xml'): '1958-01-22',
  ('1958-12-23', 'S5CV0580P0.xml'): '1958-01-23',
  ('1959-10-11', 'S5LV0305P0.xml'): '1969-10-28',
  ('1964-01-20', 'S5LV0262P0.xml'): '1965-01-20',
  ('1964-01-21', 'S5LV0262P0.xml'): '1965-01-21',
  ('1964-01-25', 'S5LV0262P0.xml'): '1965-01-25',
  ('1964-01-26', 'S5LV0262P0.xml'): '1965-01-26',
  ('1964-07-24', 'S5CV0751P0.xml'): '1967-07-24',
  ('1965-03-06', 'S5LV0196P0.xml'): '1956-03-06',
  ('1966-02-02', 'S6CV0270P0.xml'): '1996-02-02',
  ('1966-02-07', 'S5CV0634P0.xml'): '1961-02-07',
  ('1966-07-04', 'S5CV0634P0.xml'): '1961-02-17',   # WTF?
  ('1966-09-03', 'S5CV0725P0.xml'): '1966-03-09',
  ('1966-12-22', 'S5LV0273P0.xml'): '1966-02-22',
  ('1968-07-06', 'S5CV0731P0.xml'): '1966-07-06',
  ('1969-05-11', 'S5CV0790P0.xml'): '1969-11-05',
  ('1969-11-07', 'S5CV0735P0.xml'): '1966-11-07',
  ('1970-07-16', 'S5LV0322P0.xml'): '1971-07-16',
  ('1970-12-02', 'S5LV0307P0.xml'): '1970-02-12',
  ('1971-06-28', 'S5LV0172P0.xml'): '1951-06-28',
  ('1972-01-11', 'S5LV0336P0.xml'): '1972-11-01',
  ('1973-02-05', 'S5LV0307P0.xml'): '1970-02-05',
  ('1974-02-26', 'S5CV0433P0.xml'): '1947-02-26',
  ('1974-04-14', 'S6CV0241P0.xml'): '1994-04-14',
  ('1975-03-02', 'S5CV0901P0.xml'): '1975-12-02',
  ('1975-03-20', 'S5CV0901P0.xml'): '1975-11-20',
  ('1975-05-03', 'S5CV0569P0.xml'): '1957-05-03',
  ('1975-11-20', 'S5CV0578P0.xml'): '1957-11-20',
  ('1976-01-30', 'S5LV0398P0.xml'): '1979-01-30',
  ('1976-03-17', 'S5LV0321P0.xml'): '1971-07-08',
  ('1977-01-10', 'S5CV0941P0.xml'): '1978-01-10',
  ('1977-11-05', 'S5LV0582P0.xml'): '1997-11-05',
  ('1978-01-29', 'S6CV0109P0.xml'): '1987-01-29',
  ('1979-05-15', 'S5LV0360P0.xml'): '1975-05-15',
  ('1979-06-13', 'S5LV0393P0.xml'): '1978-06-13',
  ('1980-02-05', 'S5CV0995P1.xml'): '1980-12-05',
  ('1980-05-04', 'S5LV0496P0.xml'): '1988-05-04',
  ('1981-04-18', 'S5CV0105P0.xml'): '1918-04-18',
  ('1981-08-05', 'S5LV0031P0.xml'): '1918-08-05',
  ('1982-01-17', 'S5LV0534P0.xml'): '1992-01-17',
  ('1982-01-17', 'S6CV0035P0.xml'): '1983-01-17',
  ('1983-02-13', 'S6CV0054P0.xml'): '1984-02-13',
  ('1983-04-07', 'S5CV0334P0.xml'): '1938-04-07',
  ('1983-04-20', 'S4V0011P0.xml'): '1893-04-20',
  ('1983-04-23', 'S6CV0022P0.xml'): '1982-04-23',
  ('1983-05-09', 'S4V0012P0.xml'): '1893-05-09',
  ('1984-01-17', 'S6CV0071P0.xml'): '1985-01-17',
  ('1984-02-14', 'S5CV0461P0.xml'): '1949-02-14',
  ('1985-03-04', 'S6CV0059P0.xml'): '1984-05-04',
  ('1985-05-21', 'S5LV0467P0.xml'): '1985-10-21',
  ('1985-06-08', 'S6CV0006P0.xml'): '1981-06-08',
  ('1985-07-30', 'S5LV0211P0.xml'): '1958-07-30',
  ('1986-10-16', 'S6CV0089P0.xml'): '1986-01-16',
  ('1987-04-28', 'S4V0048P0.xml'): '1897-04-28',
  ('1987-07-09', 'S4V0050P0.xml'): '1897-07-09',
  ('1987-10-02', 'S6CV0110P0.xml'): '1987-02-10',
  ('1988-01-18', 'S6CV0145P0.xml'): '1989-01-18',
  ('1988-03-11', 'S6CV0112P0.xml'): '1987-03-11',
  ('1988-04-11', 'S6CV0017P0.xml'): '1982-02-11',
  ('1988-05-13', 'S5LV0589P0.xml'): '1998-05-13',
  ('1988-06-22', 'S5LV0591P0.xml'): '1998-06-22',
  ('1988-11-03', 'S6CV0129P0.xml'): '1988-03-11',
  ('1988-12-07', 'S5LV0595P0.xml'): '1998-12-07',
  ('1988-12-09', 'S5LV0595P0.xml'): '1998-12-09',
  ('1989-05-18', 'S5LV0467P0.xml'): '1985-10-16',
  ('1989-06-14', 'S4V0059P0.xml'): '1898-06-14',
  ('1989-12-19', 'S5LV0503P0.xml'): '1989-01-19',
  ('1990-03-02', 'S5LV0597P0.xml'): '1999-03-02',
  ('1990-06-16', 'S6CV0099P0.xml'): '1986-06-16',
  ('1991-03-14', 'S6CV0160P0.xml'): '1989-11-15',   # WTF?
  ('1991-05-17', 'S5CV0025P0.xml'): '1911-05-17',
  ('1991-11-17', 'S6CV0301P0.xml'): '1997-11-17',
  ('1991-12-13', 'S5LV0608P0.xml'): '1999-12-13',
  ('1992-01-20', 'S5LV0584P0.xml'): '1998-01-20',
  ('1992-03-30', 'S5LV0544P0.xml'): '1993-03-30',
  ('1992-04-02', 'S6CV0222P0.xml'): '1993-04-02',
  ('1992-11-05', 'S6CV0031P0.xml'): '1982-11-05',
  ('1993-02-22', 'S5LV0569P0.xml'): '1996-02-22',
  ('1993-03-24', 'S5LV0550P0.xml'): '1993-11-24',
  ('1993-05-13', 'S6CV0207P0.xml'): '1992-05-13',
  ('1993-05-16', 'S4V0012P0.xml'): '1893-05-16',
  ('1993-11-18', 'S5LV0540P0.xml'): '1992-11-18',
  ('1993-11-27', 'S5LV0523P0.xml'): '1990-11-27',
  ('1993-12-03', 'S5LV0540P0.xml'): '1992-12-03',
  ('1994-02-05', 'S5LV0577P0.xml'): '1997-02-05',
  ('19940-02-16', 'S5LV0552P0.xml'): '1994-02-16',
  ('1995-12-11', 'S5LV0533P0.xml'): '1991-12-11',
  ('19954-06-27', 'S5LV0565P0.xml'): '1995-06-27',
  ('1996-02-17', 'S5LV0576P0.xml'): '1996-12-17',
  ('1996-02-18', 'S5LV0576P0.xml'): '1996-12-18',
  ('1996-02-19', 'S5LV0576P0.xml'): '1996-12-19',
  ('1996-03-02', 'S5LV0273P0.xml'): '1966-03-02',
  ('1996-04-19', 'S5LV0518P0.xml'): '1990-04-19',
  ('1996-05-22', 'S5LV0519P0.xml'): '1990-05-22',
  ('1997-03-05', 'S6CV0111P0.xml'): '1987-03-05',
  ('1997-04-12', 'S6CV0302P0.xml'): '1997-12-04',
  ('1997-11-18', 'S5CV0939P0.xml'): '1977-11-18',
  ('1997-11-25', 'S5LV0577P0.xml'): '1997-02-06',
  ('1997-12-05', 'S5CV0940P0.xml'): '1977-12-05',
  ('1997-12-17', 'S6CV0295P0.xml'): '1997-06-17',
  ('1998-01-13', 'S5LV0491P0.xml'): '1988-01-13',
  ('1998-02-23', 'S5LV0493P0.xml'): '1988-02-23',
  ('1998-03-17', 'S5LV0494P0.xml'): '1988-03-17',
  ('1998-04-26', 'S5LV0390P0.xml'): '1978-04-26',
  ('1998-04-28', 'S6CV0132P0.xml'): '1988-04-28',
  ('1998-04-29', 'S6CV0132P0.xml'): '1988-04-29',
  ('1998-05-27', 'S6CV0134P0.xml'): '1988-05-27',
  ('1998-06-11', 'S6CV0137P0.xml'): '1988-07-11',
  ('1998-06-14', 'S6CV0137P0.xml'): '1988-07-14',
  ('1998-07-21', 'S6CV0137P0.xml'): '1988-07-21',
  ('1998-10-24', 'S6CV0139P0.xml'): '1988-10-24',
  ('1998-11-01', 'S6CV0139P0.xml'): '1988-11-01',
  ('1998-11-21', 'S5LV0297P0.xml'): '1968-11-21',
  ('1998-11-29', 'S6CV0142P0.xml'): '1988-11-29',
  ('1998-12-02', 'S6CV0142P0.xml'): '1988-12-02',
  ('1998-12-07', 'S6CV0143P0.xml'): '1988-12-07',
  ('1998-12-21', 'S5LV0502P0.xml'): '1988-12-22',
  ('1999-07-12', 'S5LV0530P0.xml'): '1991-07-12',
  ('1999-11-03', 'S6CV0139P0.xml'): '1988-11-03',
  ('1999-11-07', 'S5LV0532P0.xml'): '1991-11-07',
  ('2000-01-09', 'S5LV0630P0.xml'): '2002-01-09',
  ('2000-03-06', 'S6CV0381P0.xml'): '2002-03-06',
  ('2000-05-08', 'S6CV0385P0.xml'): '2002-05-08',
  ('2000-10-04', 'S6CV0348P0.xml'): '2000-04-10',
  ('2000-11-07', 'S5LV0245P0.xml'): '1962-12-20',
  ('2000-11-07', 'S6CV0412P0.xml'): '2003-10-27',  # There are multiple uses of this date that are wrong, but none have text associated with them, so it doesn't matter
  ('2001-01-14', 'S5LV0630P0.xml'): '2002-01-14',
  ('2001-05-11', 'S6CV0374P0.xml'): '2001-11-05',
  ('2001-08-02', 'S6CV0362P0.xml'): '2001-02-08',
  ('2001-11-19', 'S6CV0129P0.xml'): '1988-03-07',
  ('2001-12-17', 'S5LV0620P0.xml'): '2001-01-17',
  ('2002-04-09', 'S6CV0403P0.xml'): '2003-04-09',
  ('2002-07-19', 'S6CV0354P1.xml'): '2000-07-19',
  ('2002-11-06', 'S6CV0371P0.xml'): '2001-07-11',
  ('2002-12-06', 'S6CV0376P0.xml'): '2001-12-06',
  ('2002-12-20', 'S5LV0630P0.xml'): '2001-12-20',
  ('2003-03-10', 'S6CV0345P0.xml'): '2000-03-10',
  ('2003-04-11', 'S6CV0412P0.xml'): '2003-11-04',
  ('2003-05-02', 'S6CV0384P0.xml'): '2002-05-02',
  ('2004-05-06', 'S5LV0650P0.xml'): '2003-05-06',
  ('2004-07-01', 'S6CV0416P1.xml'): '2004-01-07',
  ('2004-10-02', 'S6CV0418P1.xml'): '2004-03-02',
  ('2004-12-19', 'S6CV0396P0.xml'): '2002-12-19',
  ('2005-05-15', 'S6CV0385P0.xml'): '2002-05-15',
  ('2006-03-20', 'S6CV0354P1.xml'): '2000-07-18',  # There are multiple uses of this date that are wrong, but none have text associated with them, so it doesn't matter
  ('2006-03-20', 'S6CV0412P0.xml'): '2003-10-29',
  ('2006-04-14', 'S6CV0403P0.xml'): '2003-04-14',
  ('2006-04-24', 'S6CV0354P1.xml'): '2000-07-20',  # There are multiple uses of this date that are wrong, but none have text associated with them, so it doesn't matter
  ('2974-06-30', 'S5CV0878P0.xml'): '1974-07-30',
  ('8976-05-10', 'S5LV0370P0.xml'): '1976-05-10',
}

def date_it(node, filename):
  assert node.tag == 'date'
  date = node.attrib['format'].strip()
  if (date, filename) in DATE_FIXES:
    date = DATE_FIXES[(date, filename)]
  return date

def texts_for_house(house, filename):
  for n in house.iter('col'):
    n.text = ''
  results = []
  for node in house.findall('*'):
    if node.find('date') is not None:
      results.append((date_it(node.find('date'), filename), all_the_text(node)))
      house.remove(node)
  results.insert(0, (date_it(house.find('date'), filename), all_the_text(house)))
  return results

def all_the_text(holder):
  return re.sub(" +", " ", " ".join(map(text_for_holder, list(holder.iter('p')))))

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

def tokenize(text, data, date, filename, house):
  lowertext = text.casefold()
  index = 0
  while index < len(lowertext):
    if lowertext[index].isalpha():
      for start, index in make_words(text, index):
        word = lowertext[start:index]
        if word not in data or data[word].date > date:
          snip_start = find_snip_boundary(lowertext, start, -1)
          snip_end = 1 + find_snip_boundary(lowertext, index-1, 1)
          snippet = text[snip_start:snip_end].strip()
          if snip_end < len(text) and text[snip_end] in ".?!":
            snippet += text[snip_end]
            if snip_end + 1 < len(text) and text[snip_end+1] == '"':
              snippet += text[snip_end+1]
          data[word] = WordData(word, date, snippet, house, filename)
    index += 1

def make_words(text, index):
  start_index = index
  starts = [index]
  results = []
  while index < len(text):
    c = text[index]
    if c.isalpha():
      index += 1
      continue
    if c == "'" or c == '-':
      if index + 1 < len(text) and text[index+1].isalpha():
        index += 1
        continue
    if c == " " and index + 1 < len(text) and text[start_index].isupper() and text[index+1].isupper():
      results.extend(map(lambda x: (x, index), starts))
      starts.append(index+1)
      index += 1
      continue
    if c == '.' and index + 1 < len(text) and text[index+1].isalpha():
      index += 1
      continue
    break
  results.extend(map(lambda x: (x, index), starts))
  return results

ALLOWED_ABBREVIATIONS = ['mr', 'mrs', 'ms', 'hon', 'esq', 'no', 'nos', '&c', 'col', 'cols']

def find_snip_boundary(lowertext, index, dir):
  keep_going = True
  while 0 <= index < len(lowertext) and keep_going:
    keep_going = False
    c = lowertext[index]
    if c.isalpha() or '0' <= c <= '9' or c in ":; ',-()&\"":
      keep_going = True
    if c == '.':
      if index >= 2 and lowertext[index-2] in ' .' and lowertext[index-1].isalpha():
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