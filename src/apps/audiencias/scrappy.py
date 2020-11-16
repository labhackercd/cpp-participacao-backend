from datetime import datetime, timedelta
from django.conf import settings
import requests


def api_get_objects(url):
    data = requests.get(url).json()
    objects = data['results']

    while(data['next']):
        print(data['next'])
        data = requests.get(data['next']).json()
        objects += data['results']

    return objects


def get_rooms(messages_period):
    if messages_period == 'all':
        url = settings.EDEMOCRACIA_URL + '/audiencias/api/room/'
    else:
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        params = '?date__gte=%s' % yesterday.strftime('%Y-%m-%d')
        url = settings.EDEMOCRACIA_URL + '/audiencias/api/room/' + params

    rooms = api_get_objects(url)

    return rooms
