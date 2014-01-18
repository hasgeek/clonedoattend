from mechanize import Browser, RobustFactory
from datetime import datetime
from .maps import maps

class Mechanizer(object):
    def __init__(self):
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
                    form[key] = data[item]['data']
                if _type == 'listcontrols':
                    form[key] = [data[item]['data']]
                if _type == 'datetimes':
                    try:
                        form[key] = datetime.strptime(data[item]['data'], '%d-%m-%Y %H:%M').strftime('%b-%d-%Y %H:%M')
                    except ValueError:
                        print "Value %s for %s is invalid. It should be formatted in DD-MM-YYYY HH:MM format" % (data[item]['data'], item)
                        sys.exit(1)
                if _type == 'dates':
                    try:
                        form[key] = datetime.strptime(data[item]['data'], '%d-%m-%Y').strftime('%b-%d-%Y')
                    except ValueError:
                        print "Value %s for %s is invalid. It should be formatted in DD-MM-YYYY format" % (data[item]['data'], item)
                        sys.exit(1)
        for _type in ['inputs', 'listcontrols', 'datetimes', 'dates']:
            if _type in m:
                fill(_type)
        return form