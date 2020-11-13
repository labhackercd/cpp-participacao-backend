
from decouple import config
from datetime import datetime, timedelta
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
import requests


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


def get_analytics_data(ga_id, start_date, end_date, metrics, dimensions=None,
                       filters=None, max_results=10000): 
    service = get_service(
        api_name='analytics',
        api_version='v3',
        scopes=[settings.GA_SCOPE],
        key_file_location=settings.GA_KEY)

    params = {
        'ids': 'ga:' + ga_id,
        'start_date': start_date,
        'end_date': end_date,
        'metrics': ','.join(metrics),
        'dimensions': ','.join(dimensions),
        'filters': filters,
        'start_index': 1,
        'max_results': max_results
    }

    first_run = True
    rows = []

    while first_run == True or results.get('nextLink'):
        if first_run == False:
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
