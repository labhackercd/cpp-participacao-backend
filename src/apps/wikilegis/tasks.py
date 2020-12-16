from participacao.celery import app
from .scraping import api_get_participations
from apps.wikilegis.models import (
    GeneralAnalysisWikilegis, DocumentAnalysisWikilegis, WikilegisGA)
from django.core.exceptions import ObjectDoesNotExist
from collections import Counter
from datetime import date, timedelta
import calendar
from django.db.models.functions import Cast, Coalesce
from django.db.models import Func, F, IntegerField, Sum
from django.db.models.expressions import Value
from django.conf import settings
from utils.data import (get_analytics_data, compile_ga_data,
                        sum_values_monthly_analysis,
                        sum_values_yearly_analysis)

FIRST_YEAR = 2019
FIRST_MONTH = 1
LAST_MONTH = 12
FIRST_DAY = 1
LAST_DAY = 31
DATA_FORMAT = '{0}-{1}-{2}'


def get_or_create_document_analyse(data):
    period = 'daily'
    data_format = remove_fields_from_data_documents(data)
    document_id = data.get('id', None)

    if document_id is None:
        raise AttributeError('Document missing id')

    try:
        analyse = DocumentAnalysisWikilegis.objects.get(document_id=data['id'])
        analyse.data = data_format
        analyse.save()
    except ObjectDoesNotExist:
        today = date.today()
        analyse = DocumentAnalysisWikilegis(
            start_date=today, data=data_format, end_date=today,
            period=period, document_id=data['id'])
    return analyse


def get_or_create_daily_analyse(data, type_analyse):
    period = 'daily'
    try:
        analyse = GeneralAnalysisWikilegis.objects.get(
            start_date=data[0], end_date=data[0], period=period)
        analyse.data[type_analyse] = data[1]
        analyse.save()
    except ObjectDoesNotExist:
        first_data = {type_analyse: data[1]}
        analyse = GeneralAnalysisWikilegis(
            start_date=data[0], data=first_data, end_date=data[0],
            period=period)

    return analyse


def get_or_create_general_analyse(start_date, end_date, data, period):
    try:
        analyse = GeneralAnalysisWikilegis.objects.get(
            start_date=start_date, end_date=end_date, period=period)
        analyse.data = data
        analyse.save()
    except ObjectDoesNotExist:
        analyse = GeneralAnalysisWikilegis.objects.create(
            start_date=start_date, data=data, end_date=end_date, period=period)

    return analyse


def count_participation(data):
    if len(data) == 0:
        raise AttributeError('Error, missing data')

    sum_data = Counter(value['created'][:10] for value in data)
    sum_data = sum_data.items()
    return sum_data


def remove_fields_from_data_documents(data):
    data.pop('slug', None)
    data.pop('description', None)
    data.pop('responsible', None)
    data.pop('owner', None)
    data.pop('pub_excerpts', None)

    return data


@app.task(name="wikilegis.get_documents")
def get_documents(periods=None):
    type_analyse = 'documents'
    if periods is None:
        periods = 'today'
    documents = api_get_participations(periods, type_analyse)
    batch_size = 100

    document_analysis = [get_or_create_document_analyse(
        data) for data in documents]

    DocumentAnalysisWikilegis.objects.bulk_create(
        document_analysis, batch_size, ignore_conflicts=True)


@app.task(name="wikilegis.get_participations")
def get_participations(periods=None, type_analyse=None):
    if not type_analyse:
        return 'Error missing type_analyse, choose votes or suggestions'
    if periods is None:
        periods = 'today'
    participations = api_get_participations(periods, type_analyse)
    participations_count = count_participation(participations)
    batch_size = 100

    general_analysis = [get_or_create_daily_analyse(
        data, type_analyse) for data in participations_count]

    GeneralAnalysisWikilegis.objects.bulk_create(
        general_analysis, batch_size, ignore_conflicts=True)


def count_data_analysis(analysis):
    votes = Cast(Func(F('data'), Value('votes'),
                      function='jsonb_extract_path_text'), IntegerField())
    suggestions = Cast(Func(F('data'), Value('suggestions'),
                            function='jsonb_extract_path_text'),
                       IntegerField())

    data = analysis.aggregate(
        votes=Coalesce(Sum(votes), 0),
        suggestions=Coalesce(Sum(suggestions), 0),
    )

    return data


@app.task(name="wikilegis.get_month_analysis")
def get_month_analysis(month=None, year=None):
    if month is None:
        today = date.today()
        last_month = today.replace(day=1) - timedelta(days=1)
        month = last_month.month
        year = last_month.year
    save_monthly_analysis(month, year)


@app.task(name="wikilegis.get_yearly_analysis")
def get_yearly_analysis(year=None):
    if year is None:
        today = date.today()
        year = today.year - 1
    save_yearly_analysis(year)


@app.task(name="wikilegis.get_all_analysis")
def get_all_analysis():
    save_all_analysis()


@app.task(name='wikilegis.get_all_period_analysis')
def get_all_period_analysis():
    today = date.today()
    LAST_YEAR = today.year
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        for month in range(FIRST_MONTH, LAST_MONTH + 1):
            if year == today.year and month == today.month:
                break
            save_monthly_analysis(month, year)
        if year < today.year:
            save_yearly_analysis(year)
    save_all_analysis()


def save_monthly_analysis(month, year):
    monthly_period = 'monthly'
    minimal_period = 'daily'

    daily_analysis = GeneralAnalysisWikilegis.objects.filter(
        period=minimal_period, start_date__month=month, start_date__year=year,
        end_date__month=month, end_date__year=year).values('data')

    if daily_analysis.count() > 0:
        range_date = calendar.monthrange(year, month)
        last_day = range_date[1]
        start_date = DATA_FORMAT.format(year, month, FIRST_DAY)
        end_date = DATA_FORMAT.format(year, month, last_day)
        data = count_data_analysis(daily_analysis)

        get_or_create_general_analyse(
            start_date, end_date, data, monthly_period)


def save_yearly_analysis(year):
    yearly_period = 'yearly'
    minimal_period = 'monthly'

    monthly_analysis = GeneralAnalysisWikilegis.objects.filter(
        period=minimal_period, start_date__year=year,
        end_date__year=year).values('data')

    if monthly_analysis.count() > 0:
        start_date = DATA_FORMAT.format(year, FIRST_MONTH, FIRST_DAY)
        end_date = DATA_FORMAT.format(year, LAST_MONTH, LAST_DAY)
        data = count_data_analysis(monthly_analysis)

        get_or_create_general_analyse(
            start_date, end_date, data, yearly_period)


def save_all_analysis():
    daily_period = 'daily'
    monthly_period = 'monthly'
    yearly_period = 'yearly'
    period = 'all'

    today = date.today()
    end_date = today - timedelta(days=1)

    year_analysis = GeneralAnalysisWikilegis.objects.filter(
        period=yearly_period)
    month_analysis = GeneralAnalysisWikilegis.objects.filter(
        period=monthly_period, start_date__year=today.year,
        end_date__year=today.year)
    daily_analysis = GeneralAnalysisWikilegis.objects.filter(
        period=daily_period, start_date__year=today.year,
        start_date__month=today.month, end_date__year=today.year,
        end_date__month=today.month)
    start_date = DATA_FORMAT.format(FIRST_YEAR, FIRST_MONTH, FIRST_DAY)

    all_analysis = year_analysis | month_analysis | daily_analysis

    data = count_data_analysis(all_analysis)

    get_or_create_general_analyse(start_date, end_date, data, period)


def get_object(ga_data, period='daily'):
    data, start_date, end_date = compile_ga_data(ga_data, period)
    ga_object = WikilegisGA(start_date=start_date, end_date=end_date,
                            data=data, period=period)

    return ga_object


@app.task(name="get_ga_wikilegis_daily")
def get_ga_wikilegis_daily(start_date=None, end_date=None, max_results=10000):
    batch_size = 100
    yesterday = date.today() - timedelta(days=1)
    metrics = ['ga:users', 'ga:newUsers', 'ga:sessions', 'ga:pageviews']
    dimensions = ['ga:date']
    filters = ['ga:pagePathLevel1=@/wikilegis']
    ga_id = settings.GA_ID_EDEMOCRACIA

    if not start_date:
        start_date = yesterday.strftime('%Y-%m-%d')

    if not end_date:
        end_date = yesterday.strftime('%Y-%m-%d')

    results = get_analytics_data(ga_id, start_date, end_date, metrics,
                                 dimensions, filters)

    ga_analysis = [get_object(result, 'daily') for result in results]

    WikilegisGA.objects.bulk_create(ga_analysis, batch_size,
                                    ignore_conflicts=True)


@app.task(name="get_ga_wikilegis_monthly")
def get_ga_wikilegis_monthly(start_date=None):
    batch_size = 100
    end_date = date.today().replace(day=1) - timedelta(days=1)

    if not start_date:
        start_date = end_date.replace(day=1)

    ga_analysis_daily = WikilegisGA.objects.filter(
        period='daily',
        start_date__gte=start_date,
        end_date__lte=end_date)

    data_by_month = sum_values_monthly_analysis(ga_analysis_daily)

    ga_analysis_monthly = [get_object(result, 'monthly')
                           for result in data_by_month]

    WikilegisGA.objects.bulk_create(ga_analysis_monthly, batch_size,
                                    ignore_conflicts=True)


@app.task(name="get_ga_wikilegis_yearly")
def get_ga_wikilegis_yearly(start_date=None):
    batch_size = 100
    end_date = date.today().replace(day=1, month=1) - timedelta(days=1)

    if not start_date:
        start_date = end_date.replace(day=1, month=1)

    ga_analysis_monthly = WikilegisGA.objects.filter(
        period='monthly',
        start_date__gte=start_date,
        end_date__lte=end_date)

    data_by_year = sum_values_yearly_analysis(ga_analysis_monthly)

    ga_analysis_yearly = [get_object(result, 'yearly')
                          for result in data_by_year]

    WikilegisGA.objects.bulk_create(ga_analysis_yearly, batch_size,
                                    ignore_conflicts=True)
