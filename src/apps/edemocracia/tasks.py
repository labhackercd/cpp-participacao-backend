from participacao.celery import app
from utils.data import get_analytics_data, get_api_objects
from .models import EdemocraciaGA, EdemocraciaAnalysis
from datetime import date, timedelta
from django.db.models.functions import TruncMonth, TruncYear, Cast
from django.db.models import Func, F, IntegerField, Sum
from django.db.models.expressions import Value
import calendar
from django.conf import settings
from collections import Counter
from utils.data import compile_ga_data


def get_object(ga_data, period='daily'):
    data, start_date, end_date = compile_ga_data(ga_data, period)
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

    ga_analysis = [get_object(result, 'daily') for result in results]

    EdemocraciaGA.objects.bulk_create(ga_analysis, batch_size,
                                      ignore_conflicts=True)


def get_data_fields():
    users = Cast(Func(F('data'), Value('users'),
                 function='jsonb_extract_path_text'), IntegerField())
    newusers = Cast(Func(F('data'), Value('newUsers'),
                    function='jsonb_extract_path_text'), IntegerField())
    sessions = Cast(Func(F('data'), Value('sessions'),
                    function='jsonb_extract_path_text'), IntegerField())
    pageviews = Cast(Func(F('data'), Value('pageViews'),
                     function='jsonb_extract_path_text'), IntegerField())

    return users, newusers, sessions, pageviews


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

    users, newusers, sessions, pageviews = get_data_fields()

    data_by_month = ga_analysis_daily.annotate(
        month=TruncMonth('start_date')).values('month').annotate(
            total_users=Sum(users), total_newusers=Sum(newusers),
            total_sessions=Sum(sessions), total_pageviews=Sum(pageviews)
            ).values('month', 'total_users', 'total_newusers',
                     'total_sessions', 'total_pageviews')

    ga_analysis_monthly = [get_object(result, 'monthly')
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

    users, newusers, sessions, pageviews = get_data_fields()

    data_by_year = ga_analysis_monthly.annotate(
        year=TruncYear('start_date')).values('year').annotate(
            total_users=Sum(users), total_newusers=Sum(newusers),
            total_sessions=Sum(sessions), total_pageviews=Sum(pageviews)
            ).values('year', 'total_users', 'total_newusers',
                     'total_sessions', 'total_pageviews')

    ga_analysis_yearly = [get_object(result, 'yearly')
                          for result in data_by_year]

    EdemocraciaGA.objects.bulk_create(ga_analysis_yearly, batch_size,
                                      ignore_conflicts=True)


def save_registers_count(registers_by_date, period='daily'):
    if period == 'daily':
        data = {'register_count': registers_by_date[1]}
        start_date = end_date = registers_by_date[0]
    else:
        data = {
            "register_count": registers_by_date['total_registers']
        }
        if period == 'monthly':
            start_date = registers_by_date['month']
            last_day = calendar.monthrange(start_date.year,
                                           start_date.month)[1]
            end_date = start_date.replace(day=last_day)

        elif period == 'yearly':
            start_date = registers_by_date['year']
            end_date = start_date.replace(day=31, month=12)

    analyse_object = EdemocraciaAnalysis(start_date=start_date,
                                         end_date=end_date,
                                         data=data, period=period)
    return analyse_object


@app.task(name="get_edemocracia_registers_daily")
def get_edemocracia_registers_daily(start_date=None):
    batch_size = 100
    yesterday = date.today() - timedelta(days=1)

    if not start_date:
        start_date = yesterday.strftime('%Y-%m-%d')

    users = get_api_objects(settings.EDEMOCRACIA_URL
                            + '/api/v1/user/?date_joined__gte='
                            + start_date)

    date_joined_list = [user['date_joined'].split('T')[0] for user in users]

    registers_by_day = Counter(date_joined_list)

    registers_daily = [save_registers_count(result, 'daily')
                       for result in registers_by_day.items()]

    EdemocraciaAnalysis.objects.bulk_create(registers_daily, batch_size,
                                            ignore_conflicts=True)


@app.task(name="get_edemocracia_registers_monthly")
def get_edemocracia_registers_monthly(start_date=None):
    batch_size = 100
    end_date = date.today().replace(day=1) - timedelta(days=1)

    if not start_date:
        start_date = end_date.replace(day=1).strftime('%Y-%m-%d')

    registers_daily = EdemocraciaAnalysis.objects.filter(
        period='daily',
        start_date__gte=start_date,
        end_date__lte=end_date.strftime('%Y-%m-%d'))

    registers_count = Cast(Func(F('data'), Value('register_count'),
                           function='jsonb_extract_path_text'), IntegerField())

    data_by_month = registers_daily.annotate(
        month=TruncMonth('start_date')).values('month').annotate(
            total_registers=Sum(registers_count)).values(
                'month', 'total_registers')

    registers_monthly = [save_registers_count(result, 'monthly')
                         for result in data_by_month]

    EdemocraciaAnalysis.objects.bulk_create(registers_monthly, batch_size,
                                            ignore_conflicts=True)


@app.task(name="get_edemocracia_registers_yearly")
def get_edemocracia_registers_yearly(start_date=None):
    batch_size = 100
    end_date = date.today().replace(day=1, month=1) - timedelta(days=1)

    if not start_date:
        start_date = end_date.replace(day=1, month=1).strftime('%Y-%m-%d')

    registers_monthly = EdemocraciaAnalysis.objects.filter(
        period='monthly',
        start_date__gte=start_date,
        end_date__lte=end_date.strftime('%Y-%m-%d'))

    registers_count = Cast(Func(F('data'), Value('register_count'),
                           function='jsonb_extract_path_text'), IntegerField())

    data_by_year = registers_monthly.annotate(
        year=TruncYear('start_date')).values('year').annotate(
            total_registers=Sum(registers_count)).values(
                'year', 'total_registers')

    registers_yearly = [save_registers_count(result, 'yearly')
                        for result in data_by_year]

    EdemocraciaAnalysis.objects.bulk_create(registers_yearly, batch_size,
                                            ignore_conflicts=True)
