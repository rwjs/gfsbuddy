#!/usr/bin/env python

from __future__ import print_function
from datetime import *
import sys
import time
import os
import argparse

__doc__ = """
NAME
	gfsbuddy

SYNOPSIS
	[PIPE] | gfsbuddy

DESCRIPTION
	This script is designed to help those running (manually-fed) tape archive
	jobs on a "Grandfather-Father-Son" rotation schedule keep track of the
	relevant tape for that day. It is written so that it can easily be modified
	for a different rotation schedule, or any other similar use case (ie,
	producing different outputs depending on time).

ENVIRONMENT VARIABLES
	STDIN_FORMAT
		Specify the format (in strftime format) of the dates handed in via stdin.
		Defaults to '%a %b %d %H:%M:%S %Z %Y'
	FORCE_STDIN
		If "true", "t", "yes", "y", or "1", force use of stdin as the format.
		Otherwise, only use stdin if it appears to be open.
		Defaults to 0 (False)

MESSAGE NOTES:
	The Message is formatted with strftime formats. Full information
	for this can be found at < http://strftime.org/ >.
	There is also an aditional extension; '%J' - the week number of month.

DEVELOPERS NOTES
	The crux of `gfsbuddy` is the TimeMap class. This takes;
		1. A unique name (which doubles up as the command-line flag)
		2. A message to show when the check matches - see MESSAGE NOTE
		3. The function to determine if the program matches.
			Takes one argument (the time to check, as a datetime object).
		4. Whether or not to enable this check.
			Defaults to False
	The program can either read from STDIN (one date per line), or if STDIN is
	empty, it will produce the relevant tape for the current date. STDIN can
	be forced by toggling the FORCE_STDIN flag. The format that is expected from
	STDIN is described by STDIN_FORMAT, the syntax of which is covered in
	the time libraries in C89/ANSI C. More detail can be found at
	http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior

AUTHOR
	Written by Robert W.J. Stewart.

TODO
	* Add more check/do functions
"""

################################## Variables ##################################

STDIN_FORMAT = os.environ.get('STDIN_FORMAT', '%a %b %d %H:%M:%S %Z %Y') # Default format of GNU/date in Linux.
FORCE_STDIN  = str(os.environ.get('FORCE_STDIN', 0)) in ('true','t','yes','y','1')

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

################################## Instances ##################################

TimeMap('last-workday-of-financial-year','End of Financial Year',      lambda t: t.weekday() == 4 and t.month == 6 and (t + timedelta(weeks=1)).month == 7)
TimeMap('last-workday-of-year',          'End of Year',                lambda t: t.weekday() == 4 and t.year != (t + timedelta(weeks=1)).year)
TimeMap('last-workday-of-month',         'End of Month',               lambda t: t.weekday() == 4 and t.month != (t + timedelta(weeks=1)).month)
TimeMap('last-workday-of-week',          '%A %J',                      lambda t: t.weekday() == 4)
TimeMap('workday',                       '%A',                         lambda t: t.weekday() in (0,1,2,3,4))
TimeMap('last-day-of-week',              'Last Day of Week',           lambda t: t.weekday() == 5)
TimeMap('last-day-of-month',             'Last Day of Month',          lambda t: t.month != (t + timedelta(days=1)).month)
TimeMap('last-day-of-year',              'Last Day of Year',           lambda t: t.year != (t + timedelta(days=1)).year)
TimeMap('last-day-of-financial-year',    'Last Day of Financial Year', lambda t: t.month == 6 and (t + timedelta(days=1)) == 7)
TimeMap('first-day-of-week',             'First Day of Week',          lambda t: t.weekday() == 6)
TimeMap('first-day-of-month',            'First Day of Month',         lambda t: t.day == 1)
TimeMap('first-day-of-year',             'First Day of Year',          lambda t: t.day == 1 and t.month == 1)
TimeMap('first-day-of-financial-year',   'First Day of Financial Year',lambda t: t.day == 1 and t.month == 7)
TimeMap('day',                           '%A',                         lambda t: True)

################################# Run program #################################

def reader():
	if FORCE_STDIN or not sys.stdin.isatty():
		# read from STDIN
		for line in sys.stdin.readlines():
			yield datetime.strptime(line.rstrip('\n'), STDIN_FORMAT)
			# strptime is a factory method for datetime() objects..
	else:
		yield datetime.now()

if __name__ == '__main__':
	# Legacy - enable workday for missing values
	TimeMap.by_name('last-workday-of-financial-year').enabled = True
	TimeMap.by_name('last-workday-of-year').enabled = True
	TimeMap.by_name('last-workday-of-month').enabled = True
	TimeMap.by_name('last-workday-of-week').enabled = True
	TimeMap.by_name('workday').enabled = True

	# Parse arguments
	ap = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
	for inst in TimeMap.Instances:
		ap.add_argument(
			'--{}'.format(inst.name)
			,nargs='?'
			,type=str
			,help='Enable this check.\n(Optionally) specify a strftime-formatted message to display.'
			,metavar='STRFTIME-FORMATTED STRING'
		)

	args = ap.parse_args()
	for key in vars(args):
		tm = TimeMap.by_name(key)
		if tm is None:
			continue
		tm.enabled = True
		if getattr(args, key) is not None:
			tm.message = getattr(args, key)

	# Run
	for line in reader():
		for instance in TimeMap.Instances:
			if instance(line):
				break
