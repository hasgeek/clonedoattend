from mechanize import ParseResponse, urlopen, urljoin, Browser, RobustFactory, LinkNotFoundError, ItemNotFoundError
from instance import config
import sys
import re
import StringIO
import unicodecsv
from .mechanizer import Mechanizer
import getpass
from helpers import title, yes_no
from urlparse import urlparse
from coaster.utils import make_name

base_uri = 'http://doattend.com/'
URI = dict(
    login=urljoin(base_uri, 'accounts/sign_in'),
    new_event=urljoin(base_uri, 'events/new'),
    overview=urljoin(base_uri, 'events/{event_id}/overview'),
    edit_event=urljoin(base_uri, 'events/{event_id}/edit'),
    ticketing_info=urljoin(base_uri, 'events/{event_id}/ticketing_options/edit'),
    tickets=urljoin(base_uri, 'events/{event_id}/tickets'),
    new_ticket=urljoin(base_uri, 'events/{event_id}/tickets/new'),
    edit_ticket=urljoin(base_uri, 'events/{event_id}/tickets/{ticket_id}/edit'),
    new_discount=urljoin(base_uri, 'events/{event_id}/discounts/new'),
    reg_form=urljoin(base_uri, 'events/{event_id}/registration_form'),
    orders=urljoin(base_uri, 'events/{event_id}/orders/registration_sheet.csv'))

class DoAttend(Mechanizer):

    def __init__(self):
        super(DoAttend, self).__init__()
        self._login()

    def _login(self):
        title("LOGIN")
        print "Logging into DoAttend..."
        self.browser.open(URI['login'])
        self.browser.select_form(nr=0)
        form = self.browser.form
        form['account[email]'] = config.get('DOATTEND_EMAIL', None) or raw_input('Please enter your registered DoAttend email address: ')
        form['account[password]'] = config.get('DOATTEND_PASS', None) or getpass.getpass('Please enter your DoAttend password: ')
        self.browser.open(form.click())
        if self.browser.geturl() == URI['login']:
            print "The credentials you provided are incorrect..."
            sys.exit(1)
        else:
            print "Successfully logged into DoAttend..."

    def create_event(self, event):
        title("CREATE EVENT")
        print "Creating Event %s, %s..." % (event['name']['data'], event['year']['data'])
        self.browser.open(URI['new_event'])
        self.browser.select_form(nr=0)
        form = self._fill_form(self.browser.form, event, 'event')
        if event['venue']['data']:
            form = self._fill_form(form, event['venue']['data'], 'venue')
        form.click()
        self.browser.open(form.click())
        self.event_id = urlparse(self.browser.geturl()).path.split('/')[2]
        print 'Event created with the ID %s' % self.event_id

    def payment_options(self, payment_info):
        title("PAYMENT INFO")
        print "Setting up payment info..."
        self.browser.open(URI['ticketing_info'].format(event_id=self.event_id))
        self.browser.select_form(nr=0)
        form = self._fill_form(self.browser.form, payment_info, 'payment_info')
        self.browser.open(form.click())
        if self.browser.geturl() == URI['tickets'].format(event_id=self.event_id):
            print "Payment info has been set..."
        else:
            print "There was an error in setting up payment info..."

    def create_tickets(self, tickets):
        def get_parent_tickets(types):
            ticks = []
            for category, tickets_of_type in tickets.iteritems():
                if category in types:
                    for ticket in tickets_of_type:
                        if 'id' in ticket:
                            ticks.append(ticket['id'])
            return ticks
        def tcreate(ticket, addon=False):
            print "Creating {} {}...".format('addon' if addon else 'ticket', ticket['name']['data'])
            self.browser.open(URI['new_ticket'].format(event_id=self.event_id))
            self.browser.select_form(nr=0)
            form = self._fill_form(self.browser.form, ticket, 'ticket')
            if addon:
                form['ticket_type[parent_ticket_ids][]'] = get_parent_tickets(ticket['addon_for']['data'])
            self.browser.open(form.click())
            if self.browser.geturl() == URI['tickets'].format(event_id=self.event_id):
                print "{} {} has been created...".format('Addon' if addon else 'Ticket', ticket['name']['data'])
            else:
                print "There was a problem creating {} {}...".format('addon' if addon else 'ticket', ticket['name']['data'])
        title("CREATE TICKETS")
        for category, tickets_of_type in tickets.iteritems():
            for ticket in tickets_of_type:
                if ticket['type']['data'] in ['ticket', 'both']:
                    tcreate(ticket)
                    pass
        self.browser.open(URI['tickets'].format(event_id=self.event_id))
        n = 0
        for category, tickets_of_type in tickets.iteritems():
            for ticket in tickets_of_type:
                if ticket['type']['data'] in ['ticket', 'both']:
                    try:
                        ticket['id'] = self.browser.find_link(text='Edit', nr=n).url.split('/')[4]
                    except LinkNotFoundError:
                        pass
                    n += 1
        title("CREATE ADDONS")
        for category, tickets_of_type in tickets.iteritems():
            for ticket in tickets_of_type:
                if ticket['type']['data'] in ['addon', 'both']:
                    tcreate(ticket, addon=True)

    def update_reg_info(self):
        fields = ['11', '10', '9', '2', '3', '5', '651']
        def add_field(field, nr):
            self.browser.open(URI['reg_form'].format(event_id=self.event_id))
            self.browser.select_form(nr=nr)
            form = self.browser.form
            try:
                form['info_id'] = [field]
            except ItemNotFoundError:
                return
            self.browser.open(form.click())
        title("ADD REGISTRATION FORM FIELDS")
        print "Adding registration fields..."
        for field in fields:
            add_field(field, 1)
        fields = ['2385']
        for field in fields:
            add_field(field, 2)
        print "Registration fields added..."
        print "Marking mandatory fields..."
        form['reqd_info[]'] = self._get_reg_info_field_ids()[:6]
        self.browser.open(form.click())
        print "Mandatory fields marked..."

    def _get_reg_info_field_ids(self, reqd=False):
        self.browser.open(URI['reg_form'].format(event_id=self.event_id))
        self.browser.select_form(nr=0)
        form = self.browser.form
        if reqd:
            return (form.find_control(name='reqd_info[]').possible_items(), form['reqd_info[]'])
        else:
            return form.find_control(name='reqd_info[]').possible_items()

    def set_event_id(self, event_id):
        print "Validating Event ID %s..." % event_id
        self.browser.open(URI['overview'].format(event_id=event_id))
        is_valid = self.browser.geturl() == URI['overview'].format(event_id=event_id)
        if not is_valid:
            print "The Event ID %s is either invalid or not for an event owned by you..." % event_id
            return False
        else:
            self.event_id = event_id
            title = self.get_event_title()
            if title:
                print "Event set to %s, %s..." % (event_id, title)
            else:
                print "Event set to %s..." % event_id
            return True

    def event_id_input(self):
        is_valid = False
        accepted = False
        while not is_valid or not accepted:
            event_id = raw_input("Please enter the DoAttend event ID: ")
            is_valid = self.set_event_id(event_id)
            if is_valid:
                title = self.get_event_title()
                self.event_title = title
                if title:
                    accepted = yes_no("Is %s the correct event?" % title)
                else:
                    accepted = yes_no("Could not retrieve the title for the event. Please check %s to confirm if %s is the correct event. Is it the correct event?" % (self.doattend.get_url(), event_id))

    def get_event_title(self):
        if self.browser.geturl() != URI['overview'].format(event_id=self.event_id):
            self.browser.open(URI['overview'].format(event_id=self.event_id))
        response = self.browser.response().read()
        matches = re.search('<h3>(.+)</h3>', response)
        return matches.group(1) if matches else ""

    def get_url(self):
        return self.browser.geturl()

    def get_discountable_tickets(self):
        print "Fetching details for discountable tickets..."
        self.browser.open(URI['new_discount'].format(event_id=self.event_id))
        self.browser.select_form(nr=0)
        ticket_ids = self.browser.form.find_control('discount[ticket_type_ids][]').possible_items()
        tickets = []
        for ticket_id in ticket_ids:
            self.browser.open(URI['edit_ticket'].format(event_id=self.event_id, ticket_id=ticket_id))
            self.browser.select_form(nr=0)
            tickets.append({'id': ticket_id, 'name': self.browser.form['ticket_type[name]'], 'max': self.browser.form['ticket_type[max_qty]']})
        print "%s discountable tickets fetched..." % len(tickets)
        return tickets

    def create_discount(self, discount):
        self.browser.open(URI['new_discount'].format(event_id=self.event_id))
        self.browser.select_form(nr=0)
        form = self._fill_form(self.browser.form, discount, 'discount')
        form['discount[ticket_type_ids][]'] = [ticket['id'] for ticket in discount['tickets']['data']]
        self.browser.open(form.click())

    def get_orders(self):
        self.browser.open(URI['orders'].format(event_id=self.event_id))
        csv_data = self.browser.response().read()
        f = StringIO.StringIO(csv_data)
        headers = [make_name(field).replace(u'-', u'').replace(u'\n', u'') for field in f.next().split(',')]
        orders = unicodecsv.reader(f, delimiter=',')
        def indexof(name):
            try:
                return headers.index(name)
            except ValueError:
                return None
        columns = dict(
            ticket_number=indexof(u'ticketnumber'),
            name=indexof(u'name'),
            email=indexof(u'email'),
            company=indexof(u'company'),
            job=indexof(u'jobtitle'),
            city=indexof(u'city'),
            phone=indexof(u'phone'),
            twitter=indexof(u'twitterhandle'),
            regdate=indexof(u'date'),
            order_id=indexof(u'orderid'),
            ticket_type=indexof(u'ticketname'),
            addons=indexof(u'addonspurchased')
            )
        return [{column:order[columns[column]] for column in columns if columns[column]} for order in orders]

    def get_booking_url(self):
        self.browser.open(URI['edit_event'].format(event_id=self.event_id))
        self.browser.select_form(nr=0)
        return 'https://' + self.browser.form['event[subdomain]'] + '.doattend.com'

    def book_ticket(self, tickets, people, code=None):
        print "Booking tickets for %s people..." % len(people)
        print "Selecting tickets%s..." % ' and applying discount code' if code else ""
        booking_url = self.get_booking_url()
        (reg_info_fields, reqd_fields) = self._get_reg_info_field_ids(reqd=True)
        self.browser.open(booking_url)
        self.browser.select_form(nr=0)
        tickets_data = dict(("qty_" + ticket, dict(data=str(len(people)))) for ticket in tickets)
        tickets_map = dict(
            inputs=dict(code='code'),
            listcontrols=dict((ticket_key, ticket_key) for ticket_key in tickets_data))
        if code:
            tickets_data['code'] = dict(data=code)
        form = self._fill_form(self.browser.form, tickets_data, tickets_map)
        self.browser.open(form.click())
        if self.browser.geturl() == urljoin(booking_url, 'orders/addons'):
            self.browser.select_form(nr=0)
            self.browser.open(self.browser.form.click())
        self.browser.select_form(nr=0)
        extra_fields = ['company', 'jobtitle', 'phone', 'city', 'twitter', 'tshirt']
        form = self._init_form(self.browser.form)
        for i, person in enumerate(people):
            print "Updating information for %s..." % person['name']
            form.set_value(person['name'], name='order[participation_attributes][][name]', nr=i)
            form.set_value(person['email'], name='order[participation_attributes][][email]', nr=i)
            for j, field in enumerate(reg_info_fields):
                # This will fail for T-shirts as it is of listcontrol type.
                # In our current use case T-shirt info is never going to be updated.
                # In case we update T-shirt info in future, we should use _fill_form and provide a custom mapper dict to it. E.g. tickets_map above
                if extra_fields[j] in person and person[extra_fields[j]]:
                    form['info_%s_%s' % (i, field)] = person[extra_fields[j]]
                elif field in reqd_fields:
                    form['info_%s_%s' % (i, field)] = "*"
        for ticket in tickets:
            form['terms_' + ticket] = ['true']
        self.browser.open(form.click())
        print "Tickets booked..."
        print self.browser.geturl()
