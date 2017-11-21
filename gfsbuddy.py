#!/usr/bin/env python

###############################################################################
#
# NAME
# gfsbuddy
#
# SYNOPSIS
# [PIPE] | gfsbuddy
#
# DESCRIPTION
# This script is designed to help those running (manually-fed) tape archive 
#  jobs on a "Grandfather-Father-Son" rotation schedule keep track of the 
#  relevant tape for that day. It is written so that it can easily be modified 
#  for a different rotation schedule, or any other similar use case (ie, 
#  producing different outputs depending on time).
#
# DEVELOPERS NOTES
# The crux of `gfsbuddy` is a pair of functions, and a 'map' to bind them
#  together. The first function in the pair is the 'check' function, which 
#  should return a boolean value indicating whether or not the day supplied 
#  passes that check (for example, it might be checking if the day is a 
#  Tuesday). The second function in the pair is the 'do' function, which returns 
#  the string to display if its paired check has passed. The 'map' is ordered; 
#  the first function-pair to pass a check has the output of its 'do' function
#  displayed, and the program terminates. 
#
# The program can either read from STDIN (one date per line), or if STDIN is
#  empty, it will produce the relevant tape for the current date. STDIN can
#  be forced by toggling the FORCE_STDIN flag. The format that is expected from
#  STDIN is described by STDIN_FORMAT, the syntax of which is covered in 
#  the time libraries in C89/ANSI C. More detail can be found at 
#  http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior
#  
# AUTHOR
# Written by Robert W.J. Stewart.
#
# TODO
# * Add support for flags/options
# * Add more check/do functions
#
###############################################################################

from __future__ import print_function
from datetime import *
import sys
import time

################################## Variables ##################################

STDIN_FORMAT = '%a %b %d %H:%M:%S %Z %Y' # Default format of GNU/date in Linux. 
FORCE_STDIN = False

class TimeMap(object):
	Instances = []
	def __init__(self, name, message, check, enabled=False):
		assert hasattr(check, '__call__'), 'check must be callable for TimeMap()'
		self.name = name
		self.message = message
		self.check = check
		self.enabled = enabled
		for idx,inst in enumerate(self.__class__.Instances):
			if inst.name == name:
				self.__class__.Instances[idx] = self
				break
		else:
			self.__class__.Instances.append(self)

	def __del__(self):
		self.__class__.Instances.pop(self.__class__.Instances.index(self))

	def __call__(self, val):
		if not self.enabled:
			return False
		elif self.check(val):
			if hasattr(self.message , '__call__'):
				print(self.message(val))
			elif type(self.message) == str:
				message = self.message.replace('%J', str(len([x for x in range(0,5) if val.month == (val - timedelta(weeks=x)).month]))) if '%J' in self.message else self.message
				print(val.strftime(message))
			else:
				print(self.message)
			return True
		return False

	def __str__(self):
		return self.name

	@classmethod
	def by_name(cls, name):
		for instance in cls.Instances:
			if instance.name == name:
				return instance

def convert_day_num(day_or_num):
	""" Convert day number (zero-indexed) to name, and visa versa """
	days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
	try:
		# Try to convert number to day
		return days[day_or_num]
	except TypeError:
		# Try to convert day to number
		return days.index(day_or_num)

################################## Instances ##################################

TimeMap('last_workday_of_financial_year','End of Financial Year',      lambda t: t.weekday() == 4 and t.month == 6 and (t + timedelta(weeks=1)).month == 7, True)
TimeMap('last_workday_of_year',          'End of Year',                lambda t: t.weekday() == 4 and t.year != (t + timedelta(weeks=1)).year,              True)
TimeMap('last_workday_of_month',         'End of Month',               lambda t: t.weekday() == 4 and t.month != (t + timedelta(weeks=1)).month,            True)
TimeMap('last_workday_of_week',          'Friday %J',                  lambda t: t.weekday() == 4,                                                          True)
TimeMap('workday',                       '%A',                         lambda t: t.weekday() in (0,1,2,3,4),                                                True)
TimeMap('last_day_of_week',              'Last Day of Week',           lambda t: t.weekday() == 5)
TimeMap('last_day_of_month',             'Last Day of Month',          lambda t: t.month != (t + timedelta(days=1)).month)
TimeMap('last_day_of_year',              'Last Day of Year',           lambda t: t.year != (t + timedelta(days=1)).year)
TimeMap('last_day_of_financial_year',    'Last Day of Financial Year', lambda t: t.month == 6 and (t + timedelta(days=1)) == 7)
TimeMap('first_day_of_week',             'First Day of Week',          lambda t: t.weekday() == 6)
TimeMap('first_day_of_month',            'First Day of Month',         lambda t: t.day == 1)
TimeMap('first_day_of_year',             'First Day of Year',          lambda t: t.day == 1 and t.month == 1)
TimeMap('first_day_of_financial_year',   'First Day of Financial Year',lambda t: t.day == 1 and t.month == 7)

################################# Run program #################################

if FORCE_STDIN or not sys.stdin.isatty():
	# read from STDIN
	def reader():
		for line in sys.stdin.readlines():
			yield datetime.strptime(line.rstrip('\n'), STDIN_FORMAT)
			# strptime is a factory method for datetime() objects..
else:
	def reader():
		yield datetime.now()

for line in reader():
	for instance in TimeMap.Instances:
		if instance(line):
			break
