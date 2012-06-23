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
#  C89/ANSI C. More detail can be found at 
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

import datetime
import sys

################################## Variables ##################################

STDIN_FORMAT = '%a %b %d %H:%M:%S %Z %Y' # Default format of GNU/date in Linux. 
FORCE_STDIN = False

############################### Check functions ###############################

# Financial Year (1 JUL -> 31 JUN); Australia/Egypt/Pakistan/New Zealand
check_end_of_financial_year = lambda t: check_end_of_week(t) and t.month == 6 and (t + datetime.timedelta(weeks=1)).month == 7
check_end_of_year = lambda t: check_end_of_week(t) and t.year != (t + datetime.timedelta(weeks=1)).year
check_end_of_month = lambda t: check_end_of_week(t) and t.month != (t + datetime.timedelta(weeks=1)).month
check_end_of_week = lambda t: t.weekday() == 4 # Friday 
check_workday = lambda t: t.weekday() in (0,1,2,3,4) # Mon/Tue/Wed/Thurs/Fri
#check_always_true = lambda t: True

################################ Do functions #################################

do_end_of_financial_year = lambda t: "End of Financial Year"
do_end_of_year = lambda t: "End of Year"
do_end_of_month = lambda t: "End of Month"
do_end_of_week = lambda t: "Friday %s" % weekcount(t)
do_workday = lambda t: convert_day_num(t.weekday())
#do_always_true = lambda t: convert_day_num(t.weekday())

##################################### Maps ####################################

maps = (	( check_end_of_financial_year, do_end_of_financial_year ),
		( check_end_of_year, do_end_of_year ),
		( check_end_of_month, do_end_of_month ),
		( check_end_of_week, do_end_of_week ),
		( check_workday, do_workday ) )

############################## Helper functions ###############################

def weekcount(day, count=1):
	""" Get the week number for day. (Recursive)"""
	lastweek = day - datetime.timedelta(weeks=1)
	if day.month != lastweek.month:
		return count
	else:
		return weekcount(lastweek, count+1)

def convert_day_num(day_or_num):
	""" Convert day number (zero-indexed) to name, and visa versa """
	days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
	try:
		# Try to convert number to day
		return days[day_or_num]
	except TypeError:
		# Try to convert day to number
		return days.index(day_or_num)

################################# Run program #################################

if FORCE_STDIN or not sys.stdin.isatty():
	# read from STDIN
	def reader():
		for line in sys.stdin.readlines():
			yield datetime.datetime.strptime(line.rstrip('\n'), STDIN_FORMAT)
else:
	def reader():
		yield datetime.datetime.now()

for line in reader():
	for check, do in maps:
		if check(line):
			print do(line)
			break
