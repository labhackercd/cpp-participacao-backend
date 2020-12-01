from datetime import datetime, timedelta
from django.conf import settings
from utils.data import get_api_objects


def api_get_rooms(messages_period):
    ROOM_AUDIENCIAS = '/audiencias/api/room/'
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    if messages_period == 'all':
        params = '?date__lte={}'.format(yesterday.strftime('%Y-%m-%d'))
    else:
        params = '?date={}'.format(yesterday.strftime('%Y-%m-%d'))

    url = settings.EDEMOCRACIA_URL + ROOM_AUDIENCIAS + params
    rooms = get_api_objects(url)

    return rooms
