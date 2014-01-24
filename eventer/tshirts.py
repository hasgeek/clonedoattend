import os
import sys
import unicodecsv
import simplejson as json
from copy import deepcopy
from urllib import urlencode
from .doattend import DoAttend
from .funnel import Funnel
from helpers import title, levenshtein
from instance import config
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from coaster.gfm import markdown
from jinja2 import Environment, PackageLoader

class Tees(object):
    emaps_dir = 'instance/.emaps'
    def __init__(self, event_id, mailer=False):
        super(Tees, self).__init__()
        if mailer:
            try:
                self.mailer = smtplib.SMTP(config['MAIL_HOST'], config['MAIL_PORT'])
            except:
                print "Error connecting with mail server. Cannot proceed..."
                sys.exit(1)
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
        count = len(tshirt_buyers)
        print "%s entries exist..." % count
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
        print "%s entries updated from DoAttend..." % (len(tshirt_buyers) - count)
        count = len(tshirt_buyers)
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
        print "%s entries updated from Funnel..." % (len(tshirt_buyers) - count)
        self.buyers = tshirt_buyers

    def email(self):
        self.download()
        title = self.doattend.get_event_title()
        path = os.path.join(self.emaps_dir, self.event_id + '_form_link')
        if os.path.exists(path):
            with open(path, 'r') as f:
                link_data = json.loads(f.read())
        else:
            fields = ['name', 'email', 'phone', 'addr1', 'addr2', 'city', 'pincode', 'state']
            link_data = dict(
                link=raw_input("Enter form URL for %s: " % title),
                fields=dict())
            for field in fields:
                link_data['fields'][field] = dict(
                    key=raw_input("Enter field name for buyer's %s: " % field),
                    value="")
            with open(path, 'w') as f:
                f.write(json.dumps(link_data))

        f = open('tshirts/%s.csv' % self.event_id, 'w')
        csv = unicodecsv.writer(f, delimiter=",", quotechar='"')
        for buyer in self.buyers:
            if buyer[4] == "0":
                print "Sending mail for %s..." % buyer[0].encode('utf-8')
                try:
                    msg = MIMEMultipart('alternative')
                    
                    msg['Subject'] = "[Urgent]Your %s T-shirt" % title
                    msg['To'] = buyer[1]
                    msg['From'] = 'support@hasgeek.com'
                    msg['Bcc'] = 'mitesh@hasgeek.com'

                    fields = ['name', 'email', 'phone', 'city']
                    form_fields = deepcopy(link_data['fields'])
                    for i, field in enumerate(fields):
                        form_fields[field]['value'] = buyer[i]
                    if buyer[5] == "1":
                        fields = ['addr1', 'addr2', 'city', 'pincode', 'state']
                        for field in fields:
                            form_fields[field]['value'] = "International"

                    link = "%s?%s" % (
                        link_data['link'],
                        urlencode(dict((field['key'], field['value'].encode('utf-8')) for key, field in form_fields.iteritems() if field['value'])))

                    env = Environment(loader=PackageLoader('eventer', 'templates'))
                    template = env.get_template('tshirt_email.md')
                    text = template.render(title=title, name=buyer[0], link=link, international=bool(int(buyer[5])), source=buyer[6])
                    html = markdown(text)

                    msg.attach(MIMEText(text.encode('utf-8'), 'plain'))
                    msg.attach(MIMEText(html.encode('utf-8'), 'html'))

                    to = [buyer[1], msg['Bcc']]
                    
                    self.mailer.sendmail(msg['From'], to, msg.as_string())

                    buyer[4] = "1"
                except:
                    print "Failed sending email for %s..." % buyer[0].encode('utf-8')
            csv.writerow(buyer)


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
    
