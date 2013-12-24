# DoAttend Event Creation Script
This is an event creation script tailor-made for easing out the creation of [HasGeek](https://hasgeek.com)'s conferences on DoAttend.

## Setup
* Checkout the repository.
* Run `pip install -r requirements.txt` inside the repo directory to install the dependencies.
* Copy `instance/settings-sample.py` to `instance/settings.py`.
* Updating the email and password is not necessary and is for convenience. If left empty, this information will be taken as an interactive input.
* The payment info is only used when the payment info is not updated in the `payment_info.csv` file for an event. Again, this is for convenience, and only useful if you are creating a lot of events at the same time.

## Usage
There is a base data and content template that is replicated for you to customize and publish an event.

* `cd` into the root folder of the script.
* Run `python manage.py new <event_name>` to create a customisable event.
* Once you run this, a folder called `events/<event_name>` will be created.
* In the `events/<event_name>` folder, customize the `event.csv`, `payment_info.csv` and the csv files in the `tickets` folder. In all csv files, you need to edit only the second column in order to customize your event.
* `cd` into the root folder of the script.
* Run `python manage.py publish <event_name>`.