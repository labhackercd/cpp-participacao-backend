from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
import requests
from datetime import date
import calendar
from django.db.models import Func, F, IntegerField
from django.db.models.expressions import Value
from django.db.models.functions import Cast


def get_service(api_name, api_version, scopes, key_file_location):
    """Get a service that communicates to a Google API.

    Args:
        api_name: The name of the api to connect to.
        api_version: The api version to connect to.
        scopes: A list auth scopes to authorize for the application.
        key_file_location: The path to a valid service account JSON key file.

    Returns:
        A service that is connected to the specified API.
    """

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        key_file_location, scopes=scopes)

    # Build the service object.
    service = build(api_name, api_version, credentials=credentials)

    return service


def get_analytics_data(ga_id, start_date, end_date, metrics=[], dimensions=[],
                       filters=[], max_results=10000):
    file_name = 'json-key-edemocracia.json'
    service = get_service(
        api_name='analytics',
        api_version='v3',
        scopes=[settings.GA_SCOPE],
        key_file_location=settings.GA_KEY_LOCATION + file_name
    )

    params = {
        'ids': 'ga:' + ga_id,
        'start_date': start_date,
        'end_date': end_date,
        'metrics': ','.join(metrics),
        'start_index': 1,
        'max_results': max_results
    }

    if filters:
        params['filters'] = ','.join(filters)
    if dimensions:
        params['dimensions'] = ','.join(dimensions)

    first_run = True
    results = {}
    rows = []

    while first_run or results.get('nextLink'):
        if not first_run:
            params['start_index'] = (int(params['start_index']) +
                                     int(params['max_results']))

        results = service.data().ga().get(**params).execute()
        rows += results['rows']
        first_run = False

    return rows


def get_api_objects(url):
    data = requests.get(url).json()
    objects = data['results']

    while(data['next']):
        data = requests.get(data['next']).json()
        objects += data['results']

    return objects


def convert_ga_date(ga_date):
    year = int(ga_date[:4])
    month = int(ga_date[4:6])
    day = int(ga_date[6:])

    new_date = date(year, month, day)

    return new_date


def compile_ga_data(ga_data, period='daily'):

    if period == 'daily':
        data = {
            "date": ga_data[0],
            "users": ga_data[1],
            "newUsers": ga_data[2],
            "sessions": ga_data[3],
            "pageViews": ga_data[4],
        }
        start_date = end_date = convert_ga_date(ga_data[0])

    else:
        data = {
            "users": ga_data['total_users'],
            "newUsers": ga_data['total_newusers'],
            "sessions": ga_data['total_sessions'],
            "pageViews": ga_data['total_pageviews'],
        }
        if period == 'monthly':
            start_date = ga_data['month']
            last_day = calendar.monthrange(start_date.year,
                                           start_date.month)[1]
            end_date = start_date.replace(day=last_day)

        elif period == 'yearly':
            start_date = ga_data['year']
            end_date = start_date.replace(day=31, month=12)

    return data, start_date, end_date


def get_ga_data_fields():
    users = Cast(Func(F('data'), Value('users'),
                 function='jsonb_extract_path_text'), IntegerField())
    newusers = Cast(Func(F('data'), Value('newUsers'),
                    function='jsonb_extract_path_text'), IntegerField())
    sessions = Cast(Func(F('data'), Value('sessions'),
                    function='jsonb_extract_path_text'), IntegerField())
    pageviews = Cast(Func(F('data'), Value('pageViews'),
                     function='jsonb_extract_path_text'), IntegerField())

    return users, newusers, sessions, pageviews
