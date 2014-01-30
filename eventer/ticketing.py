import os
import sys
import webbrowser
import getpass
import simplejson as json
from datetime import date
from collections import defaultdict
import dateutil.parser
from .doattend import DoAttend
from .funnel import Funnel
from helpers import title, levenshtein, random_discount_code

class Ticketing(object):
    efmaps_dir = 'instance/.efmaps'
    queues = dict(
        booking=[],
        cancellation=[],
        discount=[])
    def __init__(self, event_id):
        super(Ticketing, self).__init__()
        self.doattend = DoAttend()
        if not self.doattend.set_event_id(event_id):
            sys.exit(1)
        self._load_existing_orders()
        self._load_speaker_discounts()
        self.funnel = Funnel()
        self._load_proposals(event_id)
        self._select_tickets(event_id)

    def process(self):
        for email, proposal_group in self.proposals.iteritems():
            if len(proposal_group['confirmed']):
                proposal = proposal_group['confirmed'][0]
                self._book_ticket(proposal)
            elif len(proposal_group['waitlisted']):
                proposal = proposal_group['waitlisted'][0]
                self._book_ticket(proposal)
            elif len(proposal_group['cancelled']):
                proposal = proposal_group['cancelled'][0]
                ticket = self._ticket(proposal)
                if ticket and ticket['discount'] in self.speakerdiscounts:
                    self._cancel_ticket(proposal, ticket)
                if len(proposal_group['rejected']):
                    self._send_discount(proposal)
            elif len(proposal_group['rejected']):
                proposal = proposal_group['rejected'][0]
                self._send_discount(proposal)
        self._process()
    
    def _book_ticket(self, person):
        if self._ticket(person):
            print "Ticket for %s already exists..." % person['name'].encode('utf-8')
        else:
            self.queues['booking'].append(person)

    def _cancel_ticket(self, proposal, ticket):
        self.queues['cancellation'].append((proposal, ticket))

    def _send_discount(self, person):
        self.queues['discount'].append(person)
    
    def _process(self):
        self._process_bookings()
        self._process_cancellations()
        self._process_discounts()

    def _process_bookings(self):
        title("PROCESS TICKET BOOKINGS")
        # Cannot book multiple people in same order, as cancelling single tickets will not be possible
        # max_qty = min([int(ticket['max']) for ticket in self.selected_tickets])
        # index = 0
        # while index < len(people):
        #     to = index + max_qty if index + max_qty < len(people) else len(people)
        #     for i in range(index, to):
        #         people[i] = self._speaker_info(people[i])
        #     print "Book tickets for %s..." % ", ".join([person['name'].encode('utf-8') for person in people[index:to]])
        #     self.doattend.book_ticket([ticket['id'] for ticket in self.selected_tickets], people[index:to], self._discount_code(to - index))
        #     index = to
        for person in self.queues['booking']:
            person = self._speaker_info(person)
            self.doattend.book_ticket([ticket['id'] for ticket in self.selected_tickets], [person], self._discount_code(1, name="Speaker Discount"))

    def _process_cancellations(self):
        title("PROCESS TICKET CANCELLATIONS")
        for person, ticket in self.queues['cancellation']:
            webbrowser.open_new_tab(ticket['order_url'])
            getpass.getpass("Opening order page for %s. Please press ENTER once done..." % person['name'])

    def _process_discounts(self):
        title("PROCESS PROPOSER DISCOUNTS")
        print [person['name'] for person in self.queues['discount']]

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

        statuses = {2: 'confirmed', 3: 'waitlisted', 5: 'rejected', 6: 'cancelled'}

        def clean(proposal):
            proposal['speaker'] = unicode(proposal['speaker'])
            if u'(' in proposal['speaker']:
                proposal['speaker'] = u'('.join(proposal['speaker'].split('(')[:-1]).strip()
            proposal['status'] = statuses[proposal['status']]
            return proposal
        def info(proposal):
            return dict(
                name=proposal['speaker'],
                email=proposal['email'],
                phone=proposal['phone'],
                location=proposal['location'],
                url=proposal['url'],
                submitted=dateutil.parser.parse(proposal['submitted']),
                proposal=proposal)

        proposals = [clean(proposal) for proposal in self.funnel.get_proposals(proposal_space, status=statuses.keys())]
        self.proposals = defaultdict(lambda: defaultdict(list))
        for proposal in proposals:
            self.proposals[proposal['email']][proposal['status']].append(info(proposal))

    def _load_existing_orders(self):
        print "Load DoAttend orders..."
        orders = self.doattend.get_orders()
        self.orders = defaultdict(list)
        for order in orders:
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
            print "Which tickets do you want to send to proposers?"
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

    def _ticket(self, proposal):
        for order in self.orders[proposal['email']]:
            if levenshtein(order['name'], proposal['name']) <= 3:
                return order
        return None

    def _discount_code(self, qty, name="Discount", percentage=True, value=100, ending=None):
        print "Generating discount code for %s people..." % qty
        code = random_discount_code()
        self.doattend.create_discount(dict(
            percentage=dict(data='true' if percentage else 'false'),
            amt=dict(data=str(value)),
            start_date=dict(data=date.today().strftime('%d-%m-%Y')),
            end_date=dict(data=ending.strftime('%d-%m-%Y') if ending else date.today().strftime('%d-%m-%Y')),
            max_limit=dict(data=str(qty)),
            tickets=dict(data=self.selected_tickets),
            discount_name=dict(data=name),
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

    def _load_speaker_discounts(self):
        self.speakerdiscounts = []
        for discount in self.doattend.get_discounts():
            if discount['name'] == "Speaker Discount":
                self.speakerdiscounts.append(discount['code'])
