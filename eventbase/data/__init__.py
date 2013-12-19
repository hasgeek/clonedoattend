from helpers import csv2obj
import os
from jinja2 import Environment, PackageLoader

event_root =  os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
path_arr = event_root.split('/')
event_base = path_arr[len(path_arr) - 1]
if event_base != 'eventbase':
	event_base = 'events.' + event_base

env = Environment(loader=PackageLoader(event_base, 'templates'))

def render(template, **kwargs):
	template = env.get_template(template)
	return template.render(**kwargs)

event = csv2obj(os.path.join(event_root, 'data/event.csv'))
venues = {
	venue.split('.')[0]:csv2obj(os.path.join(event_root, 'data', 'venues', venue))
	for venue in os.listdir(os.path.join(event_root, 'data', 'venues'))
	}

event['venue']['data'] = venues[event['venue']['data']] if event['venue']['data'] in venues else None
event['about_event'] = dict(data=render('about_event.html', event=event))
event['contact_info'] = dict(data=render('event_contact_info.txt'))