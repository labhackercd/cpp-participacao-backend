from participacao.celery import app
from utils.data import get_analytics_data
from .models import EdemocraciaGA
from datetime import date, timedelta
from django.db.models.functions import TruncMonth, TruncYear, Cast
from django.db.models import Func, F, IntegerField, Sum
from django.db.models.expressions import Value
import calendar


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

    ga_object = EdemocraciaGA(start_date=start_date, end_date=end_date,
                              data=data, period=period)

    return ga_object


@app.task(name="get_ga_edemocracia_daily")
def get_ga_edemocracia_daily(ga_id, start_date=None, end_date=None,
                             filters=[], max_results=10000):
    batch_size = 100
    yesterday = date.today() - timedelta(days=1)
    metrics = ['ga:users', 'ga:newUsers', 'ga:sessions', 'ga:pageviews']
    dimensions = ['ga:date']

    if not start_date:
        start_date = yesterday.strftime('%Y-%m-%d')

    if not end_date:
        end_date = yesterday.strftime('%Y-%m-%d')

    results = get_analytics_data(ga_id, start_date, end_date, metrics,
                                 dimensions, filters, max_results)

    ga_analysis = [compile_ga_data(result, 'daily') for result in results]

    EdemocraciaGA.objects.bulk_create(ga_analysis, batch_size,
                                      ignore_conflicts=True)


@app.task(name="get_ga_edemocracia_monthly")
def get_ga_edemocracia_monthly(start_date=None):
    batch_size = 100
    end_date = date.today().replace(day=1) - timedelta(days=1)

    if not start_date:
        start_date = end_date.replace(day=1).strftime('%Y-%m-%d')

    ga_analysis_daily = EdemocraciaGA.objects.filter(
        period='daily',
        start_date__gte=start_date,
        end_date__lte=end_date.strftime('%Y-%m-%d'))

    users = Cast(Func(F('data'), Value('users'),
                 function='jsonb_extract_path_text'), IntegerField())
    newusers = Cast(Func(F('data'), Value('newUsers'),
                    function='jsonb_extract_path_text'), IntegerField())
    sessions = Cast(Func(F('data'), Value('sessions'),
                    function='jsonb_extract_path_text'), IntegerField())
    pageviews = Cast(Func(F('data'), Value('pageViews'),
                     function='jsonb_extract_path_text'), IntegerField())

    data_by_month = ga_analysis_daily.annotate(
        month=TruncMonth('start_date')).values('month').annotate(
            total_users=Sum(users), total_newusers=Sum(newusers),
            total_sessions=Sum(sessions), total_pageviews=Sum(pageviews)
            ).values('month', 'total_users', 'total_newusers',
                     'total_sessions', 'total_pageviews')

    ga_analysis_monthly = [compile_ga_data(result, 'monthly')
                           for result in data_by_month]

    EdemocraciaGA.objects.bulk_create(ga_analysis_monthly, batch_size,
                                      ignore_conflicts=True)


@app.task(name="get_ga_edemocracia_yearly")
def get_ga_edemocracia_yearly(start_date=None):
    batch_size = 100
    end_date = date.today().replace(day=1, month=1) - timedelta(days=1)

    if not start_date:
        start_date = end_date.replace(day=1, month=1).strftime('%Y-%m-%d')

    ga_analysis_monthly = EdemocraciaGA.objects.filter(
        period='monthly',
        start_date__gte=start_date,
        end_date__lte=end_date.strftime('%Y-%m-%d'))

    users = Cast(Func(F('data'), Value('users'),
                 function='jsonb_extract_path_text'), IntegerField())
    newusers = Cast(Func(F('data'), Value('newUsers'),
                    function='jsonb_extract_path_text'), IntegerField())
    sessions = Cast(Func(F('data'), Value('sessions'),
                    function='jsonb_extract_path_text'), IntegerField())
    pageviews = Cast(Func(F('data'), Value('pageViews'),
                     function='jsonb_extract_path_text'), IntegerField())

    data_by_year = ga_analysis_monthly.annotate(
        year=TruncYear('start_date')).values('year').annotate(
            total_users=Sum(users), total_newusers=Sum(newusers),
            total_sessions=Sum(sessions), total_pageviews=Sum(pageviews)
            ).values('year', 'total_users', 'total_newusers',
                     'total_sessions', 'total_pageviews')

    ga_analysis_yearly = [compile_ga_data(result, 'yearly')
                          for result in data_by_year]

    EdemocraciaGA.objects.bulk_create(ga_analysis_yearly, batch_size,
                                      ignore_conflicts=True)
