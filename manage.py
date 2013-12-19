#!/usr/bin/env python
from eventer import eventer
import os
import sys
import eventbase

if len(sys.argv) <= 1:
	print 'Usage: %s new' % sys.argv[0]
	sys.exit(1)
elif sys.argv[1] == 'new' or sys.argv[1] == 'publish':
	if len(sys.argv) != 3:
		print 'Usage: %s %s name_for_event' % (sys.argv[0], sys.argv[1])
		sys.exit(1)
	else:
		getattr(eventer, sys.argv[1])(sys.argv[2])

os.environ['PYTHONINSPECT'] = 'True'