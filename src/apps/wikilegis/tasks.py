from participacao.celery import app
from .scraping import api_get_participations
from apps.wikilegis.models import (
    GeneralAnalysisWikilegis, DocumentAnalysisWikilegis)
from django.core.exceptions import ObjectDoesNotExist
from collections import Counter
from datetime import date

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
