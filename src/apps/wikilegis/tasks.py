from participacao.celery import app
from .scraping import api_get_participations
from apps.wikilegis.models import (
    GeneralAnalysisWikilegis, DocumentAnalysisWikilegis)
from django.core.exceptions import ObjectDoesNotExist
from collections import Counter
from datetime import date, timedelta
import calendar
from django.db.models.functions import Cast, Coalesce
from django.db.models import Func, F, IntegerField, Sum
from django.db.models.expressions import Value

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


@app.task(name="wikilegis.get_opnion_votes")
def get_opnion_votes(periods=None):
    type_analyse = 'votes'
    if periods is None:
        periods = 'today'
    votes = api_get_participations(periods, type_analyse)
    votes_count = count_participation(votes)
    batch_size = 100

    general_analysis = [get_or_create_daily_analyse(
        data, type_analyse) for data in votes_count]

    GeneralAnalysisWikilegis.objects.bulk_create(
        general_analysis, batch_size, ignore_conflicts=True)


@app.task(name="wikilegis.get_sugestions")
def get_sugestions(periods=None):
    type_analyse = 'suggestions'
    if periods is None:
        periods = 'today'
    suggestions = api_get_participations(periods, type_analyse)
    suggestions_count = count_participation(suggestions)
    batch_size = 100

    general_analysis = [get_or_create_daily_analyse(
        data, type_analyse) for data in suggestions_count]

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
