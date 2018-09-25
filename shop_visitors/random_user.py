import json
import requests
from constants import RANDOM_USERS_URL
from datetime import datetime, date
import random


def age(birth_date):
    today = date.today()
    y = today.year - birth_date.year
    if today.month < birth_date.month or today.month == birth_date.month and today.day < birth_date.day:
        y -= 1
    return y


def generate_random_user_properties() -> dict:
    result = json.loads(
        requests.get(url=RANDOM_USERS_URL).content
    )['results'][0]
    clean_dob = clean_date(result['dob']['date'])
    today = date.today()
    return_dict = {
        'Name': '{} {}'.format(result['name']['first'].title(), result['name']['last'].title()),
        'Date of birth': clean_dob.isoformat(),
        'City': result['location']['city'].title(),
        'Postcode': result['location']['postcode'],
        'Latitude': result['location']['coordinates']['latitude'],
        'Longitude': result['location']['coordinates']['longitude'],
        'Gender': result['gender'],
        'Phone': result['phone'],
        'Mobile': result['cell'],
        'Age': age(clean_dob),
        'Email': results['email']
    }
    return return_dict


def clean_date(dirty_date: str) -> date:
    """
    The random generator sends garbage sometimes in DOB. This will insure generating good result.
    """
    try:
        birth_date = date.fromisoformat(dirty_date)
    except ValueError:
        year = random.randint(1950, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        birth_date = date(year, month, day)
    return birth_date
