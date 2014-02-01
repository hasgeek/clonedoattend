Hello {{ name }},

{% if source == "doattend" %}
Thanks for your order for the {{ title }} t-shirt!
{% elif source == "funnel" %}
We are offering a free t-shirt to all speakers at {{ title }}.
{% endif %}
{% if international %}
Please update your t-shirt size by filling in our t-shirt information form, the link to which is given below.

Since you are located outside India, **you can ignore the address fields**. We have pre-filled them for you. You can just **update your size**. We will hand your t-shirt to you during the event, at the venue.
{% else %}
We will courier the {{ title }} t-shirt to you in a few days' time. We require you to update your address and t-shirt size using our t-shirt information form, the link to which is given below.
{% endif %}

### Please fill this form at least 15 days before commencement of the event.

[Update your t-shirt preference now]({{ link }})

Reach us on support@hasgeek.com if you have any queries.

Regards,
HasGeek Team