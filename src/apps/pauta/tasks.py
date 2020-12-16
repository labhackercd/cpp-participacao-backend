from participacao.celery import app
from utils.data import (get_analytics_data, compile_ga_data,
                        sum_values_monthly_analysis,
                        sum_values_yearly_analysis,
                        get_tastypie_api_objects)
from .models import PautasGA, PautasVotesAnalysis
from datetime import date, timedelta
from django.conf import settings
from collections import Counter

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


def save_votes_count(votes_by_date, period='daily'):
    data = {'votes_count': votes_by_date[1]}
    start_date = end_date = votes_by_date[0]
    analyse_object = PautasVotesAnalysis(start_date=start_date,
                                         end_date=end_date,
                                         data=data, period=period)
    return analyse_object


@app.task(name="get_pautas_votes_daily")
def get_pautas_votes_daily(start_date=None):
    batch_size = 100
    yesterday = date.today() - timedelta(days=1)

    if not start_date:
        start_date = yesterday.strftime(DATE_FORMAT)

    votes = get_tastypie_api_objects(
        settings.EDEMOCRACIA_URL
        + '/pautaparticipativa/api/v1/vote/?datetime__gte='
        + start_date)

    date_list = [vote['datetime'].split('T')[0] for vote in votes]

    votes_by_day = Counter(date_list)

    votes_daily = [save_votes_count(result, 'daily')
                   for result in votes_by_day.items()]

    PautasVotesAnalysis.objects.bulk_create(votes_daily, batch_size,
                                            ignore_conflicts=True)
