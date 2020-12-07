from datetime import date, timedelta

import pytest
import responses
from django.conf import settings
from mixer.backend.django import mixer
from apps.wikilegis.models import (
    DocumentAnalysisWikilegis, GeneralAnalysisWikilegis)
from apps.wikilegis.tasks import (
    get_or_create_document_analyse, get_or_create_daily_analyse, get_documents,
    get_or_create_general_analyse, count_participation, get_sugestions,
    remove_fields_from_data_documents, get_opnion_votes, )
from .mock_json import (
    MOCK_JSON_VOTES, MOCK_JSON_SUGGESTIONS, MOCK_JSON_DOCUMENTS)


class TestRoomAnalysisWikilegis:
    PATH_WIKILEGIS = '/wikilegis/api/v1/'
    EXAMPLE_DOCUMENT_DATA = {'created': '2020-12-01',
                             'id': 1,
                             'slug': 'test',
                             'description': 'test',
                             'responsible': 'test',
                             'owner': 'test',
                             'pub_excerpts': 'test', }
    EXAMPLE_DATA = data = {'suggestions': 10,
                           'votes': 20,
                           }

    def test_name_app_wikilegis(self):
        from apps.wikilegis.apps import WikilegisConfig
        app = WikilegisConfig

        assert app.name == 'wikilegis'

    @pytest.mark.django_db
    def test_create_document_analyse(self):
        document = mixer.blend(DocumentAnalysisWikilegis)

        count_document = DocumentAnalysisWikilegis.objects.count()
        saved_document = DocumentAnalysisWikilegis.objects.get(id=1)

        assert count_document == 1
        assert saved_document.data == document.data
        assert saved_document.document_id == document.document_id

    def test_remove_fields_from_data_documents(self):
        document = remove_fields_from_data_documents(
            self.EXAMPLE_DOCUMENT_DATA)

        assert document.get('created', None) == '2020-12-01'
        assert document.get('slug', None) is None
        assert document.get('description', None) is None
        assert document.get('responsible', None) is None
        assert document.get('owner', None) is None
        assert document.get('pub_excerpts', None) is None

    @pytest.mark.django_db
    def test_get_or_create_document_analyse(self):
        today = date.today()
        document = get_or_create_document_analyse(self.EXAMPLE_DOCUMENT_DATA)

        assert document.start_date == today
        assert document.end_date == today
        assert document.period == 'daily'
        assert document.document_id == self.EXAMPLE_DOCUMENT_DATA['id']

    @pytest.mark.django_db
    def test_get_or_create_document_analyse_object_exist(self):
        first_document = mixer.blend(DocumentAnalysisWikilegis, data={
        }, document_id=self.EXAMPLE_DOCUMENT_DATA['id'])

        document = get_or_create_document_analyse(self.EXAMPLE_DOCUMENT_DATA)

        assert document.start_date == first_document.start_date
        assert document.end_date == first_document.end_date
        assert document.period == 'daily'
        assert document.document_id == self.EXAMPLE_DOCUMENT_DATA['id']

    @pytest.mark.django_db
    def test_get_or_create_document_analyse_without_document_id(self):
        self.EXAMPLE_DOCUMENT_DATA['id'] = None
        with pytest.raises(AttributeError) as excinfo:
            get_or_create_document_analyse(self.EXAMPLE_DOCUMENT_DATA)

        assert 'Document missing id' in str(excinfo)

    @pytest.mark.django_db
    def test_get_or_create_daily_analyse(self):
        NUMBER_OF_VOTES = 10
        type_analyse = 'votes'
        today = date.today()
        data = (today, NUMBER_OF_VOTES)
        analyse = get_or_create_daily_analyse(data, type_analyse)

        assert analyse.start_date == today
        assert analyse.end_date == today
        assert analyse.data[type_analyse] == NUMBER_OF_VOTES

    @pytest.mark.django_db
    def test_get_or_create_daily_analyse_object_exist(self):
        NUMBER_OF_VOTES = 10
        type_analyse = 'votes'
        today = date.today()
        period = 'daily'
        mixer.blend(GeneralAnalysisWikilegis, period=period,
                    start_date=today, end_date=today, data={})
        data = (today, NUMBER_OF_VOTES)
        analyse = get_or_create_daily_analyse(data, type_analyse)

        assert analyse.start_date == today
        assert analyse.end_date == today
        assert analyse.data[type_analyse] == NUMBER_OF_VOTES

    @pytest.mark.django_db
    def test_get_or_create_general_analyse(self):
        today = date.today()
        period = 'daily'
        data_analysis = {'votes': 10,
                         'suggestion': 20}
        analyse = get_or_create_general_analyse(
            today, today, data_analysis, period)

        assert analyse.start_date == today
        assert analyse.end_date == today
        assert analyse.data == data_analysis

    @pytest.mark.django_db
    def test_get_or_create_general_analyse_object_exist(self):
        today = date.today()
        period = 'daily'
        data_analysis = {'votes': 10,
                         'suggestion': 20}
        mixer.blend(GeneralAnalysisWikilegis, period=period,
                    start_date=today, end_date=today, data={})
        analyse = get_or_create_general_analyse(
            today, today, data_analysis, period)

        assert analyse.start_date == today
        assert analyse.end_date == today
        assert analyse.data == data_analysis

    def test_count_participation(self):
        participation = MOCK_JSON_VOTES['results']

        data_count = count_participation(participation)

        assert len(data_count) > 0

    def test_count_participation_data_missing(self):
        with pytest.raises(AttributeError) as excinfo:
            participation = []
            count_participation(participation)

        assert 'Error, missing data' in str(excinfo)

    @pytest.mark.django_db
    @responses.activate
    def test_task_get_all_rooms(self):
        today = date.today()
        NUMBER_OF_DOCUMENTS_IN_MOCK = 3
        today = date.today()
        yesterday = today - timedelta(days=1)
        url = settings.EDEMOCRACIA_URL + self.PATH_WIKILEGIS + 'documents/' + \
            '?created__lte={}'.format(yesterday.strftime('%Y-%m-%d'))
        responses.add(responses.GET, url, json=MOCK_JSON_DOCUMENTS, status=200)
        get_documents.apply(args=['all'])

        documents = DocumentAnalysisWikilegis.objects.all()

        assert responses.calls[0].request.url == url
        assert documents.count() == NUMBER_OF_DOCUMENTS_IN_MOCK
        assert documents.first().document_id == 6
        assert documents.first().start_date == today
        assert documents.first().end_date == today
        assert documents.first().data is not None

    @pytest.mark.django_db
    @responses.activate
    def test_task_get_today_rooms(self):
        today = date.today()
        NUMBER_OF_DOCUMENTS_IN_MOCK = 3
        today = date.today()
        yesterday = today - timedelta(days=1)
        url = settings.EDEMOCRACIA_URL + self.PATH_WIKILEGIS + 'documents/' + \
            '?created__gte={}'.format(yesterday.strftime('%Y-%m-%d'))
        responses.add(responses.GET, url, json=MOCK_JSON_DOCUMENTS, status=200)
        get_documents.apply()

        documents = DocumentAnalysisWikilegis.objects.all()

        assert responses.calls[0].request.url == url
        assert documents.count() == NUMBER_OF_DOCUMENTS_IN_MOCK
        assert documents.first().document_id == 6
        assert documents.first().start_date == today
        assert documents.first().end_date == today
        assert documents.first().data is not None

    @pytest.mark.django_db
    @responses.activate
    def test_task_all_get_opnion_votes(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        url = settings.EDEMOCRACIA_URL + self.PATH_WIKILEGIS + \
            'opnion-votes/?created__lte={}'.format(
                yesterday.strftime('%Y-%m-%d'))
        responses.add(responses.GET, url, json=MOCK_JSON_VOTES, status=200)
        get_opnion_votes.apply(args=['all'])

        documents = GeneralAnalysisWikilegis.objects.all()

        assert responses.calls[0].request.url == url
        assert documents.count() > 0
        assert documents.first().start_date == date(2019, 9, 12)
        assert documents.first().end_date == date(2019, 9, 12)
        assert documents.first().data is not None
        assert documents.first().data['votes'] > 0

    @pytest.mark.django_db
    @responses.activate
    def test_task_today_get_opnion_votes(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        url = settings.EDEMOCRACIA_URL + self.PATH_WIKILEGIS + \
            'opnion-votes/?created__gte={}'.format(
                yesterday.strftime('%Y-%m-%d'))
        responses.add(responses.GET, url, json=MOCK_JSON_VOTES, status=200)
        get_opnion_votes.apply()

        documents = GeneralAnalysisWikilegis.objects.all()

        assert responses.calls[0].request.url == url
        assert documents.count() > 0
        assert documents.first().start_date == date(2019, 9, 12)
        assert documents.first().end_date == date(2019, 9, 12)
        assert documents.first().data is not None
        assert documents.first().data['votes'] > 0

    @pytest.mark.django_db
    @responses.activate
    def test_task_all_get_sugestions(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        url = settings.EDEMOCRACIA_URL + self.PATH_WIKILEGIS + \
            'sugestions/?created__lte={}'.format(
                yesterday.strftime('%Y-%m-%d'))
        responses.add(responses.GET, url,
                      json=MOCK_JSON_SUGGESTIONS, status=200)
        get_sugestions.apply(args=['all'])

        documents = GeneralAnalysisWikilegis.objects.all()

        assert responses.calls[0].request.url == url
        assert documents.count() > 0
        assert documents.first().start_date == date(2019, 9, 17)
        assert documents.first().end_date == date(2019, 9, 17)
        assert documents.first().data is not None
        assert documents.first().data['suggestions'] > 0

    @pytest.mark.django_db
    @responses.activate
    def test_task_today_get_sugestions(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        url = settings.EDEMOCRACIA_URL + self.PATH_WIKILEGIS + \
            'sugestions/?created__gte={}'.format(
                yesterday.strftime('%Y-%m-%d'))
        responses.add(responses.GET, url,
                      json=MOCK_JSON_SUGGESTIONS, status=200)
        get_sugestions.apply()

        documents = GeneralAnalysisWikilegis.objects.all()

        assert responses.calls[0].request.url == url
        assert documents.count() > 0
        assert documents.first().start_date == date(2019, 9, 17)
        assert documents.first().end_date == date(2019, 9, 17)
        assert documents.first().data is not None
        assert documents.first().data['suggestions'] > 0
