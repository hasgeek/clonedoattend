from mechanize import Browser, RobustFactory
from datetime import datetime
from mx import DateTime

import sys
from .maps import maps

class Mechanizer(object):
    def __init__(self, browser=None):
        if browser:
            self.browser = browser
        else:
            self.browser = Browser(factory=RobustFactory())
        return super(Mechanizer, self).__init__()

    def _init_form(self, form):
        form.set_all_readonly(False)
        return form

    def _fill_form(self, form, data, mapper):
        form = self._init_form(form)
        if data is None:
            return form
        if type(mapper) == dict:
            m = mapper
        else:
            m = maps[mapper]
        def fill(_type):
            for key, item in m[_type].items():
                if _type == 'inputs':
                    form[key] = data[item]['data'].encode('utf-8')
                if _type == 'listcontrols':
                    form[key] = [data[item]['data'].encode('utf-8')]
                if _type == 'datetimes':
                    form[key] = DateTime.Parser.DateTimeFromString(data[item]['data'].encode('utf-8')).strftime('%b-%d-%Y %H:%M')
                if _type == 'dates':
                    form[key] = DateTime.Parser.DateTimeFromString(data[item]['data'].encode('utf-8')).strftime('%b-%d-%Y')
        for _type in ['inputs', 'listcontrols', 'datetimes', 'dates']:
            if _type in m:
                fill(_type)
        return form
