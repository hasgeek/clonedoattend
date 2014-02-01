Hello {{ discount['name']['data'].split(' ')[0] }},

Please find below {{ discount['codes']['data'] }} discount code{% if discount['codes']['data'] > 1 %}s{% endif %} {%- if title %} for {{ title }}{%- endif -%}.

{% for code in codes -%}
* {{ code }}
{% endfor %}

{% if discount['codes']['data'] == 1 %}This code is{% else %}These codes are{% endif %} valid for a single use upto {{ discount['end_date']['data'] }} for the following tickets:

{% for ticket in discount['tickets']['data'] -%}
* {{ ticket['name'] }}
{% endfor %}

Thanks,
HasGeek Team
