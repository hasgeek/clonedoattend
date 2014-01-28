import os
import sys
import webbrowser
import simplejson as json
from datetime import date
from .doattend import DoAttend
from .funnel import Funnel
from helpers import title, levenshtein, random_discount_code

class Ticketing(object):
    efmaps_dir = 'instance/.efmaps'
    speakers = {}
    def __init__(self, event_id):
        super(Ticketing, self).__init__()
        self.doattend = DoAttend()
        if not self.doattend.set_event_id(event_id):
            sys.exit(1)
        self._load_existing_orders()
        self.funnel = Funnel()
        self._load_proposals(event_id)
        self._select_tickets(event_id)

    def create(self):
        title("SEND TICKETS TO SPEAKERS")
        print "There are %s confirmed proposals..." % len(self.proposals)
        people = []
        for proposal in self.proposals:
            if self._ticket_exists(proposal['email'], proposal['speaker']):
                print "Ticket for %s already exists..." % proposal['speaker'].encode('utf-8')
            elif proposal['email'] not in self.speakers:
                speaker=dict(
                    name=proposal['speaker'],
                    email=proposal['email'],
                    phone=proposal['phone'],
                    proposal=proposal)
                self.speakers[proposal['email']] = speaker
                people.append(speaker)
        max_qty = min([int(ticket['max']) for ticket in self.selected_tickets])
        index = 0
        while index < len(people):
            to = index + max_qty if index + max_qty < len(people) else len(people)
            for i in range(index, to):
                people[i] = self._speaker_info(people[i])
            print "Book tickets for %s..." % ", ".join([person['name'].encode('utf-8') for person in people[index:to]])
            self.doattend.book_ticket([ticket['id'] for ticket in self.selected_tickets], people[index:to], self._discount_code(to - index))
            index = to
            
    def _load_proposals(self, event_id):
        path = os.path.join(self.efmaps_dir, event_id)
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
            if u'(' in proposal['speaker']:
                proposal['speaker'] = u'('.join(proposal['speaker'].split('(')[:-1]).strip()

    def _load_existing_orders(self):
        print "Load DoAttend orders..."
        orders = self.doattend.get_orders()
        self.orders = {}
        for order in orders:
            if order['email'] not in self.orders:
                self.orders[order['email']] = []
            self.orders[order['email']].append(order)
        print "DoAttend orders loaded..."

    def _select_tickets(self, event_id):
        path = os.path.join(self.efmaps_dir, event_id + '_tickets')
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.selected_tickets = json.loads(f.read())
                f.close()
            return
        self.discountable_tickets = self.doattend.get_discountable_tickets()
        while True:
            print "Which tickets do you want to send to speakers?"
            for i, ticket in enumerate(self.discountable_tickets):
                print '\t' + str(i+1) + '.', ticket['name']
            self.selected_tickets = [int(ticket.strip()) for ticket in raw_input("Please enter comma-separated numbers of the tickets: ").split(',')]
            try:
                for i, ticket in enumerate(self.selected_tickets):
                    self.selected_tickets[i] = self.discountable_tickets[ticket - 1]
                with open(path, 'w') as f:
                    f.write(json.dumps(self.selected_tickets))
                    f.close()
                return
            except IndexError:
                print "Invalid input..."

    def _ticket_exists(self, email, name):
        if email in self.orders:
            for order in self.orders[email]:
                if levenshtein(order['name'], name) <= 3:
                    return True
        return False

    def _discount_code(self, qty):
        print "Generating discount code for %s people..." % qty
        code = random_discount_code()
        self.doattend.create_discount(dict(
            percentage=dict(data='true'),
            amt=dict(data="100"),
            start_date=dict(data=date.today().strftime('%d-%m-%Y')),
            end_date=dict(data=date.today().strftime('%d-%m-%Y')),
            max_limit=dict(data=str(qty)),
            tickets=dict(data=self.selected_tickets),
            discount_name=dict(data="Speaker Discount"),
            code=dict(data=code)
            ))
        print "Discount code generated..."
        return code

    def _speaker_info(self, speaker):
        print "Opening proposal page for %s's proposal..." % speaker['name'].encode('utf-8')
        webbrowser.open_new_tab(speaker['proposal']['url'])
        speaker['company'] = raw_input("Enter the company for %s: " % speaker['name'].encode('utf-8'))
        speaker['jobtitle'] = raw_input("Enter the job title for %s: " % speaker['name'].encode('utf-8'))
        speaker['twitter'] = raw_input("Enter the twitter handle for %s: " % speaker['name'].encode('utf-8'))
        speaker['city'] = raw_input("Enter the city for %s: " % speaker['name'].encode('utf-8'))
        return speaker
