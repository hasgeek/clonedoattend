from mechanize import ParseResponse, urlopen, urljoin, LinkNotFoundError, ItemNotFoundError
from instance import config
from .mechanizer import Mechanizer
import getpass
import simplejson as json
import sys
from helpers import title

base_uri = config.get('FUNNEL_URL', 'https://funnel.hasgeek.com/')
base_lastuser_uri = config.get('LASTUSER_URL', 'https://auth.hasgeek.com/')
URI = dict(
    login=urljoin(base_uri, 'login'),
    lastuser_login=urljoin(base_lastuser_uri, 'login'),
    proposal_json=urljoin(base_uri, '{space}/json'))

class Funnel(Mechanizer):
    def __init__(self, browser=None):
        super(Funnel, self).__init__(browser)
        self._login()

    def _login(self):
        title("LOGIN")
        print "Logging into Funnel..."
        self.browser.open(URI['login'])
        self.browser.select_form(nr=1)
        form = self.browser.form
        form['username'] = config.get('FUNNEL_USERNAME', None) or raw_input('Please enter your registered Funnel username: ')
        form['password'] = config.get('FUNNEL_PASSWORD', None) or getpass.getpass('Please enter your Funnel password: ')
        self.browser.open(form.click())
        if self.browser.geturl() == URI['lastuser_login']:
            print "The credentials you provided are incorrect..."
            sys.exit(1)
        else:
            print "Successfully logged into Funnel..."

    def get_proposals(self, proposal_space, **filters):
        if not hasattr(self, 'proposals'):
            print "Fetching proposals..."
            self.browser.open(URI['proposal_json'].format(space=proposal_space))
            self.proposals = json.loads(self.browser.response().read())['proposals']
            print "Proposals fetched..."
        def include(proposal):
            for key, value in filters.iteritems():
                try:
                    if type(value) == list:
                        if proposal[key] not in value:
                            return False
                    else:
                        if proposal[key] != value:
                            return False
                except KeyError:
                    return False
            return True
        return [proposal for proposal in self.proposals if include(proposal)]

