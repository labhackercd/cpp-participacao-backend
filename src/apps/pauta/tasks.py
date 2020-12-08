from participacao.celery import app
from utils.data import get_analytics_data
from .models import PautasGA
from datetime import date, timedelta
from utils.data import compile_ga_data


def get_object(ga_data, period='daily'):
    data, start_date, end_date = compile_ga_data(ga_data, period)
    ga_object = PautasGA(start_date=start_date, end_date=end_date,
                         data=data, period=period)

    return ga_object


@app.task(name="get_ga_pautas_daily")
def get_ga_pautas_daily(ga_id, start_date=None, end_date=None):
    batch_size = 100
    yesterday = date.today() - timedelta(days=1)
    metrics = ['ga:users', 'ga:newUsers', 'ga:sessions', 'ga:pageviews']
    dimensions = ['ga:date']
    filters = ['ga:pagePathLevel1=@/pautaparticipativa']

    if not start_date:
        start_date = yesterday.strftime('%Y-%m-%d')

    if not end_date:
        end_date = yesterday.strftime('%Y-%m-%d')

    results = get_analytics_data(ga_id, start_date, end_date, metrics,
                                 dimensions, filters)

    ga_analysis = [get_object(result, 'daily') for result in results]

    PautasGA.objects.bulk_create(ga_analysis, batch_size,
                                 ignore_conflicts=True)
