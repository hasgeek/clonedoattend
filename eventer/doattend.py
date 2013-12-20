from mechanize import ParseResponse, urlopen, urljoin, Browser, RobustFactory
from instance import config
import sys
from .maps import maps
from helpers import title
from datetime import datetime
from urlparse import urlparse

base_uri = 'http://doattend.com/'
URI = dict(
    login=urljoin(base_uri, 'accounts/sign_in'),
    new_event=urljoin(base_uri, 'events/new'),
    ticketing_info=urljoin(base_uri, 'events/{event_id}/ticketing_options/edit'),
    tickets=urljoin(base_uri, 'events/{event_id}/tickets'))

class DoAttend(object):

    def __init__(self):
        self.browser = Browser(factory=RobustFactory())
        self.email = config.get('DOATTEND_EMAIL', None) or raw_input('Please enter your registered DoAttend email address: ')
        self.password = config.get('DOATTEND_PASS', None) or getpass.getpass('Please enter your DoAttend password: ')
        self._login()
        return super(DoAttend, self).__init__()

    def _login(self):
        title("LOGIN")
        print "Logging into DoAttend..."
        self.browser.open(URI['login'])
        self.browser.select_form(nr=0)
        form = self.browser.form
        form['account[email]'] = self.email
        form['account[password]'] = self.password
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

    def _fill_form(self, form, data, mapper):
        m = maps[mapper]
        form.set_all_readonly(False)
        def fill(_type):
            for key, item in m[_type].items():
                if _type == 'inputs':
                    form[key] = data[item]['data']
                if _type == 'listcontrols':
                    form[key] = [data[item]['data']]
                if _type == 'dates':
                    try:
                        form[key] = datetime.strptime(data[item]['data'], '%d-%m-%Y %H:%M').strftime('%b-%d-%Y %H:%M')
                    except ValueError:
                        print "Value %s for %s is invalid. It should be formatted in DD-MM-YYYY HH:MM format" % (data[item]['data'], item)
                        sys.exit(1)
        for _type in ['inputs', 'listcontrols', 'dates']:
            if _type in m:
                fill(_type)
        return form
