from forex_python.converter import CurrencyCodes
from pytz import all_timezones
import pycountry

currency_codes = CurrencyCodes()
TIMEZONE_CHOICES = [(tz, tz) for tz in all_timezones]
COMMON_CURRENCY_CODES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'SEK', 'NZD', 'SGD', 'HKD', 'KRW', 'INR', 'BRL', 'MXN', 'ZAR', 'AED', 'TRY', 'RUB', 'NOK', 'DKK']
CURRENCY_CHOICE = [(code, currency_codes.get_currency_name(code)) for code in COMMON_CURRENCY_CODES]
ISO_CODE_CHOICES = tuple([(country.alpha_2, country.name) for country in pycountry.countries])
CONTINENT_CHOICES = (
    ('EU', 'Europe'),
    ('NA', 'North America'),
    ('SA', 'South America'),
    ('AF', 'Africa'),
    ('AS', 'Asia'),
    ('OC', 'Oceania'),
    ('AN', 'Antarctica')
)

PRESENCE_CHOICE = (
    ('online', 'Online'),
    ('away', 'Away'),
    ('offline', 'Offline')
)
