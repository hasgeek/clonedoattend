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
    'datetimes': { # All fields that are Date inputs. They should be in the format DD-MM-YYYY HH:MM & use 24-hour format
        'event[start_date]': 'start',
        'event[end_date]': 'end'
    }
}

maps['venue'] = {
    'inputs': {
        'event[venue]': 'venue',
        'event[add_1]': 'add_1',
        'event[add_2]': 'add_2',
        'event[city]': 'city',
        'event[state]': 'state',
        'event[postal_code]': 'postal_code'
    },
    'listcontrols': {
        'event[country]': 'country'
    }
}

maps['payment_info'] = {
    'inputs': {
        'payment_options[acc_name]': 'acc_name',
        'payment_options[acc_number]': 'acc_number',
        'payment_options[bank]': 'bank',
        'payment_options[branch_add]': 'branch_add',
        'payment_options[ifsc]': 'ifsc',
        'payment_options[name_on_receipt]': 'name_on_receipt'
    },
    'listcontrols': {
        'payment_options[is_paid]': 'is_paid',
        'payment_options[currency]': 'currency',
        'payment_options[acc_type]': 'acc_type'
    }
}

maps['ticket'] = {
    'inputs': {
        'ticket_type[name]': 'name',
        'ticket_type[price]': 'price',
        'ticket_type[available_number]': 'available_number',
        'ticket_type[min_qty]': 'min_qty',
        'ticket_type[max_qty]': 'max_qty',
        'ticket_type[terms]': 'info',
        'ticket_type[more_info]': 'info'
    },
    'dates': {
        'ticket_type[sales_open]': 'sales_open',
        'ticket_type[sales_close]': 'sales_close'
    }
}

maps['discount'] = {
    'inputs': {
        'discount[name]': 'discount_name',
        'discount[amt]': 'amt',
        'discount[max_limit]': 'max_limit',
        'discount[code]': 'code'
    },
    'dates': {
        'discount[start_date]': 'start_date',
        'discount[end_date]': 'end_date'
    },
    'listcontrols': {
        'discount[percentage]': 'percentage'
    }
}