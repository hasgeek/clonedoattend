Hi {{ person['name'].split(' ')[0] }},

Thanks for submitting a proposal for {{ title }}.

When your proposal was submitted, the {{ slot_ticket['name'] }} ticket(Rs. {{ int(float(slot_ticket['price'])) }}) was active.

Currently, the {{ book_ticket['name'] }} ticket(Rs. {{ int(float(book_ticket['price'])) }}) is active till {{ book_ticket['end_date'].strftime('%d %b, %Y') }}.

{% if slot_ticket['id'] == book_ticket['id'] %}
Since both of these tickets are the same, you will not require a discount code. You can straightaway go and book your ticket!
{% elif int(float(book_ticket['price'])) <= int(float(slot_ticket['price'])) %}
Since the current ticket price is either lesser or the same as the time when you booked the ticket, you will not require a discount code. You can straightaway go and book your ticket!
{% else %}
Your discount code is {{ person['code'] }}.

It's value is Rs. {{ int(float(book_ticket['price'])) - int(float(slot_ticket['price'])) }} and is valid on a single purchase of a {{ book_ticket['name'] }} ticket till {{ book_ticket['end_date'].strftime('%d %b, %Y') }}.
{% endif %}

Thanks,
Team HasGeek
