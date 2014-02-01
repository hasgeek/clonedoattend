import os
import sys
import unicodecsv
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from coaster.gfm import markdown
from jinja2 import Environment, PackageLoader
from instance import config
from .doattend import DoAttend
from helpers import title, random_discount_code

class Discounter(object):
    discounts_dir = 'discounts'
    discount_files = []
    fields = ['name', 'email', 'codes', 'end_date', 'type', 'amt']
    labels = [
        'Name of person for whom the discount is being generated',
        'Email address',
        'Number of codes to generate',
        'Discount valid till',
        'Discount Type[Accepted values = percentage, amount]',
        'Discount Value. For eg. 12 for 12%, 200 for 200 INR'
    ]

    def __init__(self):
        for discount in os.listdir(self.discounts_dir):
            if discount.split('.')[-1:][0] == 'csv':
                self.discount_files.append(discount)
        try:
            self.mailer = smtplib.SMTP(config['MAIL_HOST'], config['MAIL_PORT'])
        except:
            print "Error connecting with mail server. Cannot proceed..."
            sys.exit(1)

    def inputs(self):
        self._select_discount()
        self.doattend = DoAttend()
        self.doattend.event_id_input()
        self.event_title = self.doattend.get_event_title()
        self._collect_email_info()

    def generate(self):
        tickets = self.doattend.get_discountable_tickets()

        for discount in self.discounts:
            codes = self._create_discount(discount, tickets)
            self._send_discounts_email(discount, codes)

    @classmethod
    def help(cls):
        print "Please place your CSV file in the '%s' directory with the following columns in exactly the order given below:" % cls.discounts_dir
        for i, label in enumerate(cls.labels):
            print '\t' + str(i+1) + '.', label
    
    def _select_discount(self):
        if not len(self.discount_files):
            print "No discount code files available in the %s directory..." % self.discounts_dir
            Discounter.help()
            sys.exit(1)
        print "Please select the discount codes file:"
        for i, discount in enumerate(self.discount_files):
            print '\t' + str(i + 1) + '.', discount
        discount_index = None
        while discount_index is None or discount_index < 0 or discount_index >= len(self.discount_files):
            if discount_index is not None:
                print "Invalid input %s, your input should be between %s & %s ..." % (discount_index+1, 1, len(self.discount_files))
            discount_index = int(raw_input("Enter the number of the CSV file you'd like to use: ")) - 1
            self.discount_index = discount_index
        self._load_discounts()

    def _create_discount(self, discount, tickets):
        def select_tickets(discount):
            while True:
                print "For which tickets do you want to give %s(%s) %s discount codes?" % (discount['name']['data'], discount['email']['data'], discount['codes']['data'])
                for i, ticket in enumerate(tickets):
                    print '\t' + str(i+1) + '.', ticket['name']
                selected_tickets = [int(ticket.strip()) for ticket in raw_input("Please enter comma-separated numbers of the tickets: ").split(',')]
                try:
                    for i, ticket in enumerate(selected_tickets):
                        selected_tickets[i] = tickets[ticket - 1]
                    return selected_tickets
                except IndexError:
                    print "Invalid input..."
        codes = []
        discount['percentage'] = {'data': 'true' if discount['type']['data'] == 'percentage' else 'false'}
        discount['start_date'] = {'data': date.today().strftime('%d-%m-%Y')}
        discount['max_limit'] = {'data': '1'}
        selected_tickets = select_tickets(discount)
        discount['tickets'] = {'data': selected_tickets}
        try:
            discount['codes']['data'] = int(discount['codes']['data'])
        except ValueError:
            discount['codes']['data'] = 1
        for i in range(discount['codes']['data']):
            code = random_discount_code()
            discount['discount_name'] = {
                'data': '.'.join(self.discount_files[self.discount_index].split('.')[:-1]) + ' %s %s' % (discount['email']['data'], i + 1)}
            codes.append(code)
            discount['code'] = {'data': code}
            self.doattend.create_discount(discount)
        return codes

    def _send_discounts_email(self, discount, codes):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Your discount code%s%s" % (
            "s" if len(codes) > 1 else "",
            " for " + self.event_title if self.event_title else "")
        msg['From'] = self.email_info['from_email']
        msg['To'] = discount['email']['data']
        if self.email_info['cc']:
            msg['CC'] = self.email_info['cc']
        msg['BCC'] = 'mitesh@hasgeek.com'
        if self.email_info['replyto'] and  self.email_info['replyto'] != self.email_info['from_email']:
            msg['Reply-To'] = self.email_info['replyto']

        env = Environment(loader=PackageLoader('eventer', 'templates'))
        template = env.get_template('discount_email.md')
        
        text = template.render(discount=discount, title=self.event_title, codes=codes)
        html = markdown(text)

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        to = [discount['email']['data'], 'mitesh@hasgeek.com']
        if self.email_info['cc'] != "":
            to = to + self.email_info['cc'].split(',')

        self.mailer.sendmail(self.email_info['from_email'], to, msg.as_string())



    def _load_discounts(self):
        print "Loading discounts..."
        f = open(os.path.join(self.discounts_dir, self.discount_files[self.discount_index]))
        csv = unicodecsv.reader(f, delimiter=",", quotechar='"')
        self.discounts = []
        for row in csv:
            if len(row) < len(self.fields):
                print "Omitting %s. Inadequate number of columns..." % row[0]
            else:
                self.discounts.append({})
                for column, value in enumerate(row):
                    self.discounts[len(self.discounts) - 1][self.fields[column]] = dict(data=value, helper=u"")
        print "%s discounts loaded..." % len(self.discounts)


    def _collect_email_info(self):
        self.email_info = dict(
            from_email=raw_input("From email address: "),
            replyto=raw_input("Reply-to email address[If different from the 'From' address]: "),
            cc=raw_input("Comma-separated CC addresses: "))

