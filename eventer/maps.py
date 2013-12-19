maps = {}

maps['event'] = {
	'inputs': { # All fields that take string inputs
		'event[title]': 'name',
		'event[about]': 'about_event',
		'event[subdomain]': 'subdomain',
		'event[contact_info]': 'contact_info',
		'event[website]': 'website'
	},
	'listcontrols': { # All fields that are ListControl inputs. Includes select, radios, checkboxes
		'event[time_zone]': 'timezone'
	},
	'dates': { # All fields that are Date inputs. They should be in the format DD-MM-YYYY HH:MM & use 24-hour format
		'event[start_date]': 'start',
		'event[end_date]': 'end'
	}
}