#!/usr/bin/env python
from eventer import eventer, Discounter
import os
import sys
import eventbase

if len(sys.argv) <= 1:
    print 'Usage: %s new|publish|discounts|tickets|tshirts' % sys.argv[0]
    sys.exit(1)
elif sys.argv[1] == 'new' or sys.argv[1] == 'publish':
    if len(sys.argv) != 3:
        print 'Usage: %s %s name_for_event' % (sys.argv[0], sys.argv[1])
        sys.exit(1)
    else:
        getattr(eventer, sys.argv[1])(sys.argv[2])
elif sys.argv[1] == 'discounts':
    if len(sys.argv) != 3 or sys.argv[2] != 'create':
        print 'Usage: %s discounts create' % sys.argv[0]
        Discounter.help()
        sys.exit(1)
    else:
        eventer.discounts()
elif sys.argv[1] == 'tickets':
    if len(sys.argv) != 3:
        print 'Usage: %s tickets event_id' % sys.argv[0]
        sys.exit(1)
    else:
        eventer.tickets(sys.argv[2])
elif sys.argv[1] == 'tshirts':
    if len(sys.argv) != 4 or not eventer.tshirts(sys.argv[2], sys.argv[3]):
        print 'Usage: %s tshirts download|email event_id' % sys.argv[0]
