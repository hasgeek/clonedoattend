from mechanize import ParseResponse, urlopen, urljoin, Browser
from instance import config
import sys
from .maps import maps
from datetime import datetime
from urlparse import urlparse

base_uri = 'http://doattend.com/'
URI = dict(
    login=urljoin(base_uri, 'accounts/sign_in'),
    new_event=urljoin(base_uri, 'events/new'))

class DoAttend(object):

    def __init__(self):
        self.email = config.get('DOATTEND_EMAIL', None) or raw_input('Please enter your registered DoAttend email address: ')
        self.password = config.get('DOATTEND_PASS', None) or getpass.getpass('Please enter your DoAttend password: ')
        self._login()
        return super(DoAttend, self).__init__()

    def _login(self):
        print "Logging into DoAttend..."
        forms = ParseResponse(urlopen(URI['login']))
        form = forms[0]
        form['account[email]'] = self.email
        form['account[password]'] = self.password
        response = urlopen(form.click())
        if response.geturl() == URI['login']:
            print "The credentials you provided are incorrect..."
            sys.exit(1)
        else:
            print "Successfully logged into DoAttend..."

    def create_event(self, event):
        print "Creating Event %s, %s..." % (event['name']['data'], event['year']['data'])
        forms = ParseResponse(urlopen(URI['new_event']))
        form = self._fill_form(forms[0], event, 'event')
        if event['venue']['data']:
            form = self._fill_form(forms[0], event['venue']['data'], 'venue')
        form.click()
        response = urlopen(form.click())
        self.event_id = urlparse(response.geturl()).path.split('/')[2]
        print 'Event created with the ID %s' % self.event_id

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
