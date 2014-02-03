import os
import sys
import webbrowser
import getpass
import unicodecsv
import simplejson as json
import pickle
from datetime import date, datetime
from collections import defaultdict
import dateutil.parser
from .doattend import DoAttend
from .funnel import Funnel
from helpers import title, levenshtein, random_discount_code
from instance import config
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from coaster.gfm import markdown
from jinja2 import Environment, PackageLoader

class Ticketing(object):
    efmaps_dir = 'instance/.efmaps'
    queues = dict(
        booking=[],
        cancellation=[],
        discount=[])
    sent_discounts = defaultdict(lambda: None)
    def __init__(self, event_id):
        super(Ticketing, self).__init__()
        try:
            self.mailer = smtplib.SMTP(config['MAIL_HOST'], config['MAIL_PORT'])
        except:
            print "Error connecting with mail server. Cannot proceed..."
            sys.exit(1)
        self.doattend = DoAttend()
        if not self.doattend.set_event_id(event_id):
            sys.exit(1)
        self._load_existing_orders()
        self.event_title = self.doattend.get_event_title()

    def process(self):
        self._load_speaker_discounts()
        self._select_tickets()
        self._select_tickets(conference=True)
        self._load_sent_discounts()
        self.funnel = Funnel()
        self._load_proposals()
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

    def show_duplicates(self):
        title("SHOWING DUPLICATE TICKET HOLDERS")
        for email, order in self.orders.iteritems():
            tickets = []
            status = False
            for ticket in order:
                if ticket['ticket_type'] in tickets:
                    status = True
                tickets.append(ticket['ticket_type'])
                if ticket['addons']:
                    tickets.append(ticket['addons'])
            if status:
                title("EMAIL:" + email.upper())
                print "Name\t\t\t | Phone\t | Order ID\t | Ticket ID\t | Ticket Type\t\t\t | Addons\t |"
                for ticket in order:
                    print ticket['name'] + ('\t' if len(ticket['name']) < 16 else '') + '\t | ' + ticket['phone'] + '\t | ' + ticket['order_id'] + '\t | ' + ticket['ticket_number'] + '\t | ' + ticket['ticket_type'] + '\t | ' + ticket['addons'] + '\t |'
    def _book_ticket(self, person):
        if self._ticket(person):
            print "Ticket for %s already exists..." % person['name'].encode('utf-8')
        else:
            self.queues['booking'].append(person)

    def _cancel_ticket(self, proposal, ticket):
        self.queues['cancellation'].append((proposal, ticket))

    def _send_discount(self, person):
        record = self.sent_discounts[person['email']]
        if not record or record[2] == "0":
            try:
                person['code'] = record[1] if bool(record[1]) else None
            except TypeError:
                person['code'] = None
            self.queues['discount'].append(person)

    def _load_sent_discounts(self):
        self.sent_discounts_path = os.path.join(self.efmaps_dir, self.doattend.event_id + '_proposer_discounts.csv')
        if not os.path.exists(self.sent_discounts_path):
            with open(self.sent_discounts_path, 'w') as f:
                f.close()
        self.sent_discounts_file = open(self.sent_discounts_path, 'r+')
        csv = unicodecsv.reader(self.sent_discounts_file, delimiter=",", quotechar='"')
        for proposer in csv:
            self.sent_discounts[proposer[0]] = proposer
    
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
        title("PROCESS PROPOSAL DISCOUNTS")
        csv = unicodecsv.writer(self.sent_discounts_file, delimiter=",", quotechar='"')
        for person in self.queues['discount']:
            now = datetime.now()
            person['submitted'] = person['submitted'].replace(tzinfo=None)
            slot_ticket, book_ticket = None, None
            for ticket in self.conf_tickets:
                if not slot_ticket and ticket['start_date'].date() <= person['submitted'].date() and person['submitted'].date() <= ticket['end_date'].date():
                    slot_ticket = ticket
                if not book_ticket and ticket['start_date'].date() <= now.date() and now.date() <= ticket['end_date'].date():
                    book_ticket = ticket
            if not person['code'] and book_ticket != slot_ticket:
                person['code'] = self._discount_code(1, "Proposal Discount", percentage=False, value=int(float(book_ticket['price'])) - int(float(slot_ticket['price'])), ending=book_ticket['end_date'])
            if not self.sent_discounts[person['email']]:
                self.sent_discounts[person['email']] = [person['email'], person["code"], "0"]
                csv.writerow(self.sent_discounts[person['email']])
            if person['code'] or int(float(book_ticket['price'])) <= int(float(slot_ticket['price'])):
                self.sent_discounts[person['email']][1] = person['code']
                try:
                    self._discount_email(person, book_ticket, slot_ticket)
                    self.sent_discounts[person['email']][2] = "1"
                    print "Discount code sent to %s..." % person['name']
                except:
                    print "Unable to send discount code email to %s..." % person['name']
        with open(self.sent_discounts_path, 'w') as f:
            csv = unicodecsv.writer(f, delimiter=",", quotechar='"')
            for discount in self.sent_discounts.values():
                csv.writerow(discount)

    def _discount_email(self, person, book_ticket, slot_ticket):
        msg = MIMEMultipart('alternative')
        
        msg['Subject'] = "%s Discount Code" % self.event_title
        msg['To'] = person['email']
        msg['From'] = 'support@hasgeek.com'
        msg['Bcc'] = 'mitesh@hasgeek.com'

        env = Environment(loader=PackageLoader('eventer', 'templates'))
        template_name = self.doattend.event_id + '_proposal_discount_email.md'
        path = os.path.join('eventer', 'templates', 'custom', template_name)
        if os.path.exists(path):
            template = env.get_template('custom/' + template_name)
        else:
            template = env.get_template('proposal_discount_email.md')
        text = template.render(title=self.event_title, person=person, book_ticket=book_ticket, slot_ticket=slot_ticket, float=float, int=int)
        html = markdown(text)

        msg.attach(MIMEText(text.encode('utf-8'), 'plain'))
        msg.attach(MIMEText(html.encode('utf-8'), 'html'))

        to = [person['email'], msg['Bcc']]
        
        self.mailer.sendmail(msg['From'], to, msg.as_string())

    def _load_proposals(self):
        path = os.path.join(self.efmaps_dir, self.doattend.event_id)
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

    def _select_tickets(self, conference=False):
        if conference:
            path = os.path.join(self.efmaps_dir, self.doattend.event_id + '_conf_tickets')
        else:
            path = os.path.join(self.efmaps_dir, self.doattend.event_id + '_tickets')
        if os.path.exists(path):
            with open(path, 'r') as f:
                if conference:
                    self.conf_tickets = pickle.load(f)
                else:
                    self.selected_tickets = json.loads(f.read())
                f.close()
            return
        if not hasattr(self, 'discountable_tickets'):
            self.discountable_tickets = self.doattend.get_discountable_tickets()
        while True:
            if conference:
                print "Which of these tickets are conference tickets?"
            else:
                print "Which tickets do you want to send to proposers?"
            for i, ticket in enumerate(self.discountable_tickets):
                print '\t' + str(i+1) + '.', ticket['name']
            tickets = [int(ticket.strip()) for ticket in raw_input("Please enter comma-separated numbers of the tickets: ").split(',')]
            try:
                for i, ticket in enumerate(tickets):
                    tickets[i] = self.discountable_tickets[ticket - 1]
                with open(path, 'w') as f:
                    if conference:
                        self.conf_tickets = tickets
                        pickle.dump(tickets, f)
                    else:
                        f.write(json.dumps(ticket))
                        self.selected_tickets = tickets
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
            start_date=dict(data=date.today().strftime('%m-%d-%Y')),
            end_date=dict(data=ending.strftime('%m-%d-%Y') if ending else date.today().strftime('%m-%d-%Y')),
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
