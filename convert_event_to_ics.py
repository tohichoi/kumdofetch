#!/usr/bin/env python
import sys
import os
from ics import Calendar, Event
import unittest
import pendulum
import re

def parse_date(s):
	# pattern1 : 00월 00일
	# pattern2 : 00월 00일 ~ 00월 00일
	s = re.sub('00', '01', s)
	dates = re.findall(r'(\d\d월 \d\d일)', s)
	try:
		b = None
		e = None
		b = pendulum.from_format(dates[0], 'MM월 DD일').date()
		e = pendulum.from_format(dates[1], 'MM월 DD일').date()
	except Exception as ex:
		pass
	finally:		
		return b, e

def make_event(lines):
	L = []
	keys = ('subject', 'date', 'location', 'host')
	for line in lines:
		l = line.strip()
		if len(l) < 1:
			continue
		L.append(l)

	assert(len(keys), len(L))

	print(L)
	event = dict(zip(keys, L))

	e = Event()
	e.name = event['subject']
	bd, ed = parse_date(event['date'])
	e.begin = bd.isoformat()
	if ed:
		e.end = ed.isoformat()
	e.organizer = event['host']
	e.location = event['location']

	return e

def main():
	with open(sys.argv[1]) as fd:
		c = Calendar()
		lines = fd.readlines()
		for i in range(int(len(lines)/4)):
			buffer = lines[i*4:i*4+4]
			e = make_event(buffer)
			c.events.add(e)
		
	print(c.events)

	with open('event.ics', 'w') as f:
	    f.writelines(c.serialize_iter())

	
class Test(unittest.TestCase):
	def test_parse_date(self):
		s=[('11월 04일', pendulum.date(2023, 11, 4), None), 
			('11월 10일 ~ 11월 12일', pendulum.date(2023, 11, 10), pendulum.date(2023, 11, 12)),
			('07월 00일', pendulum.date(2023, 7, 1), None)]

		for d in s:
			b, e = parse_date(d[0])
			self.assertEqual(b, d[1])
			self.assertEqual(e, d[2])


if __name__ == '__main__':
	main()

