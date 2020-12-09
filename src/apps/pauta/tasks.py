from participacao.celery import app
from utils.data import get_analytics_data, compile_ga_data, get_ga_data_fields
from .models import PautasGA
from datetime import date, timedelta
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models import Sum


DATE_FORMAT = '%Y-%m-%d'


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

    users, newusers, sessions, pageviews = get_ga_data_fields()

    data_by_month = ga_analysis_daily.annotate(
        month=TruncMonth('start_date')).values('month').annotate(
            total_users=Sum(users), total_newusers=Sum(newusers),
            total_sessions=Sum(sessions), total_pageviews=Sum(pageviews)
            ).values('month', 'total_users', 'total_newusers',
                     'total_sessions', 'total_pageviews')

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

    users, newusers, sessions, pageviews = get_ga_data_fields()

    data_by_year = ga_analysis_monthly.annotate(
        year=TruncYear('start_date')).values('year').annotate(
            total_users=Sum(users), total_newusers=Sum(newusers),
            total_sessions=Sum(sessions), total_pageviews=Sum(pageviews)
            ).values('year', 'total_users', 'total_newusers',
                     'total_sessions', 'total_pageviews')

    ga_analysis_yearly = [get_object(result, 'yearly')
                          for result in data_by_year]

    PautasGA.objects.bulk_create(ga_analysis_yearly, batch_size,
                                 ignore_conflicts=True)
