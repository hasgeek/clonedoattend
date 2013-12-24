import getpass
import os
import sys
import shutil
from .doattend import DoAttend
from instance import config
from helpers import yes_no
from importlib import import_module


class Eventer(object):
    def __init__(self):
        if not os.path.exists('events'):
            os.mkdir('events')
        if not os.path.exists('events/__init__.py'):
            with open('events/__init__.py', 'w'):
                pass
    def new(self, event):
        path = 'events/%s' % event
        if os.path.exists(path):
            if yes_no('%s already exists. Do you want to replace it?' % event):
                shutil.rmtree(path)
            else:
                sys.exit(1)
        shutil.copytree('eventbase', path)
        print "Event created in %s. Please edit the data and templates as required by you." % event

    def publish(self, event):
        path = 'events/%s' % event
        if not os.path.exists(path):
            print "Invalid event %s" % event
        else:
            self.doattend = DoAttend()
            event_module = import_module('events.%s' % event)
            self.doattend.create_event(event_module.event)
            self.doattend.payment_options(event_module.payment_info)
            self.doattend.create_tickets(event_module.tickets)
            self.doattend.update_reg_info()


eventer = Eventer()