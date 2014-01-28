#!/usr/bin/env python

import os
from mechanize import Browser, RobustFactory
from eventer.doattend import DoAttend
from eventer.funnel import Funnel
from helpers import yes_no

browser = Browser(factory=RobustFactory())
print "Mechanize browser is available in object 'browser'..."
if yes_no("Log into DoAttend? "):
	doattend = DoAttend(browser)
	print "Use the object 'doattend' to take actions..."

if yes_no("Log into Funnel? "):
	funnel = Funnel(browser)
	print "Use the object 'funnel' to take actions..."

os.environ['PYTHONINSPECT'] = 'True'
