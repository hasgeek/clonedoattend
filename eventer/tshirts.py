import os
import sys
import unicodecsv
from .doattend import DoAttend
from .funnel import Funnel
from helpers import title, levenshtein

class Tees(object):
    emaps_dir = 'instance/.emaps'
    def __init__(self, event_id):
        super(Tees, self).__init__()
        self.doattend = DoAttend()
        if not self.doattend.set_event_id(event_id):
            sys.exit(1)
        self._load_existing_orders()
        self.funnel = Funnel()
        self._load_proposals(event_id)
        self.event_id = event_id

    def _load_proposals(self, event_id):
        path = os.path.join(self.emaps_dir, event_id)
        if os.path.exists(path):
            with open(path, 'r') as f:
                proposal_space = f.read()
                f.close()
        else:
            proposal_space = raw_input('Please enter the name of the Funnel Proposal Space: ')
            with open(path, 'w') as f:
                f.write(proposal_space)
                f.close()
        self.proposals = self.funnel.get_proposals(proposal_space, confirmed=True)
        for proposal in self.proposals:
            proposal['speaker'] = unicode(proposal['speaker'])
            proposal['speaker'] = u'('.join(proposal['speaker'].split('(')[:-1]).strip()

    def download(self):
        f = open('tshirts/%s.csv' % self.event_id, 'r+')
        csv = unicodecsv.reader(f, delimiter=",", quotechar='"')
        tshirt_buyers = []
        done = {}
        def add_done(buyer):
            if buyer[1] not in done:
                done[buyer[1]] = []
            done[buyer[1]].append(buyer[0])
        def international(buyer):
            return str(int(buyer[2][0] == '+' and buyer[2][:3] != '+91'))
        def should_add(buyer):
            if buyer[1] in done:
                for d in done[buyer[1]]:
                    if levenshtein(buyer[0], d) <= 3:
                        return False
            return True
        for buyer in csv:
            tshirt_buyers.append(buyer)
            add_done(buyer)
        csv = unicodecsv.writer(f, delimiter=",", quotechar='"')
        for order in self.orders:
            buyer = [order['name'], order['email'], order['phone'], order['city'], "0"]
            buyer.append(international(buyer))
            buyer.append("doattend")
            buyer.append(order['order_id'])
            if (u'Corporate' in order['ticket_type'] or 'T-shirt' in order['addons']) and should_add(buyer):
                csv.writerow(buyer)
                tshirt_buyers.append(buyer)
                add_done(buyer)
        for proposal in self.proposals:
            order = self._ticket(proposal['email'], proposal['speaker'])
            if order:
                buyer = [order['name'], order['email'], order['phone'], order['city'], "0"]
            else:
                buyer = [proposal['speaker'], proposal['email'], proposal['phone'], "", "0"]
            buyer.append(international(buyer))
            buyer.append("funnel")
            buyer.append(proposal['url'])
            if should_add(buyer):
                csv.writerow(buyer)
                tshirt_buyers.append(buyer)
                add_done(buyer)


    def _load_existing_orders(self):
        print "Load DoAttend orders..."
        self.orders = self.doattend.get_orders()
        self.orders_by_email = {}
        for order in self.orders:
            if order['email'] not in self.orders_by_email:
                self.orders_by_email[order['email']] = []
            self.orders_by_email[order['email']].append(order)
        print "DoAttend orders loaded..."

    def _ticket(self, email, name):
        if email in self.orders_by_email:
            for order in self.orders_by_email[email]:
                if levenshtein(order['name'], name) <= 3:
                    return order
        return None
    
