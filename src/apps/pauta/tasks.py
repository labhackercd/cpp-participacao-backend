from participacao.celery import app
from utils.data import (get_analytics_data, compile_ga_data,
                        sum_values_monthly_analysis,
                        sum_values_yearly_analysis)
from .models import PautasGA
from datetime import date, timedelta
from django.conf import settings

DATE_FORMAT = '%Y-%m-%d'


def get_object(ga_data, period='daily'):
    data, start_date, end_date = compile_ga_data(ga_data, period)
    ga_object = PautasGA(start_date=start_date, end_date=end_date,
                         data=data, period=period)

    return ga_object


@app.task(name="get_ga_pautas_daily")
def get_ga_pautas_daily(start_date=None, end_date=None):
    batch_size = 100
    yesterday = date.today() - timedelta(days=1)
    metrics = ['ga:users', 'ga:newUsers', 'ga:sessions', 'ga:pageviews']
    dimensions = ['ga:date']
    filters = ['ga:pagePathLevel1=@/pautaparticipativa']
    ga_id = settings.GA_ID_EDEMOCRACIA

    if not start_date:
        start_date = yesterday.strftime(DATE_FORMAT)

    if not end_date:
        end_date = yesterday.strftime(DATE_FORMAT)

    results = get_analytics_data(ga_id, start_date, end_date, metrics,
                                 dimensions, filters)

    ga_analysis = [get_object(result, 'daily') for result in results]

    PautasGA.objects.bulk_create(ga_analysis, batch_size,
                                 ignore_conflicts=True)


@app.task(name="get_ga_pautas_monthly")
def get_ga_pautas_monthly(start_date=None):
    batch_size = 100
    end_date = date.today().replace(day=1) - timedelta(days=1)

    if not start_date:
        start_date = end_date.replace(day=1).strftime(DATE_FORMAT)

    ga_analysis_daily = PautasGA.objects.filter(
        period='daily',
        start_date__gte=start_date,
        end_date__lte=end_date.strftime(DATE_FORMAT))

    data_by_month = sum_values_monthly_analysis(ga_analysis_daily)

    ga_analysis_monthly = [get_object(result, 'monthly')
                           for result in data_by_month]

    PautasGA.objects.bulk_create(ga_analysis_monthly, batch_size,
                                 ignore_conflicts=True)


@app.task(name="get_ga_pautas_yearly")
def get_ga_pautas_yearly(start_date=None):
    batch_size = 100
    end_date = date.today().replace(day=1, month=1) - timedelta(days=1)

    if not start_date:
        start_date = end_date.replace(day=1, month=1).strftime(DATE_FORMAT)

    ga_analysis_monthly = PautasGA.objects.filter(
        period='monthly',
        start_date__gte=start_date,
        end_date__lte=end_date.strftime(DATE_FORMAT))

    data_by_year = sum_values_yearly_analysis(ga_analysis_monthly)

    ga_analysis_yearly = [get_object(result, 'yearly')
                          for result in data_by_year]

    PautasGA.objects.bulk_create(ga_analysis_yearly, batch_size,
                                 ignore_conflicts=True)
