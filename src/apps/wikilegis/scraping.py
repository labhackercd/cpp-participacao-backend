from datetime import datetime, timedelta
from django.conf import settings
from utils.data import get_api_objects


def api_get_participations(messages_period, type_object):
    URL_WIKILEGIS = '/wikilegis/api/v1/'
    if type_object == 'documents':
        PATH = 'documents/'
    elif type_object == 'suggestions':
        PATH = 'sugestions/'
    else:
        PATH = 'opnion-votes/'
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    if messages_period == 'all':
        params = '?created__lte={}'.format(yesterday.strftime('%Y-%m-%d'))
    else:
        params = '?created__gte={}'.format(yesterday.strftime('%Y-%m-%d'))

    url = settings.EDEMOCRACIA_URL + URL_WIKILEGIS + PATH + params
    objects = get_api_objects(url)

    return objects
