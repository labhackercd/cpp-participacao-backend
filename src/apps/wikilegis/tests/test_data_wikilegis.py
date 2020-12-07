from datetime import date, timedelta
import calendar
import pytest
import responses
from django.conf import settings
from mixer.backend.django import mixer
from random import randrange

from apps.wikilegis.models import (
    DocumentAnalysisWikilegis, GeneralAnalysisWikilegis)
from apps.wikilegis.tasks import (
    get_or_create_document_analyse, get_or_create_daily_analyse, get_documents,
    get_or_create_general_analyse, count_participation, get_sugestions,
    remove_fields_from_data_documents, get_opnion_votes, count_data_analysis,
    save_monthly_analysis, save_yearly_analysis, save_all_analysis,
    get_month_analysis, get_yearly_analysis, get_all_analysis,
    get_all_period_analysis)
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

    @pytest.mark.django_db
    def test_daily_analysis(self):
        period = 'daily'
        NUMBER_ANALYSIS = 5
        mixer.cycle(NUMBER_ANALYSIS).blend(
            GeneralAnalysisWikilegis, data=self.EXAMPLE_DATA, period=period)

        daily_analysis = GeneralAnalysisWikilegis.objects.all().values('data')

        data = count_data_analysis(daily_analysis)

        assert data['suggestions'] == NUMBER_ANALYSIS * \
            self.EXAMPLE_DATA['suggestions']
        assert data['votes'] == NUMBER_ANALYSIS * \
            self.EXAMPLE_DATA['votes']

    @pytest.mark.django_db
    def test_save_monthly_analysis(self):
        NUMBER_ANALYSIS = 5
        period = 'monthly'
        today = date.today()
        random_date = today.replace(day=1)

        for count in range(NUMBER_ANALYSIS):
            mixer.blend(GeneralAnalysisWikilegis, period='daily',
                        start_date=random_date + timedelta(days=count),
                        end_date=random_date + timedelta(days=count),
                        data=self.EXAMPLE_DATA)

        save_monthly_analysis(today.month, today.year)

        monthly_analysis = GeneralAnalysisWikilegis.objects.filter(
            period=period)

        assert GeneralAnalysisWikilegis.objects.count() == NUMBER_ANALYSIS + 1
        assert monthly_analysis.count() == 1
        assert monthly_analysis.first(
        ).data['votes'] == self.EXAMPLE_DATA['votes'] * NUMBER_ANALYSIS
        assert monthly_analysis.first(
        ).data['suggestions'] == self.EXAMPLE_DATA['suggestions'] * \
            NUMBER_ANALYSIS

    @pytest.mark.django_db
    def test_save_yearly_analysis(self):
        NUMBER_ANALYSIS = 5
        period = 'yearly'
        today = date.today()
        random_date = date(today.year, 1, 1)

        for count in range(NUMBER_ANALYSIS):
            mixer.blend(GeneralAnalysisWikilegis, period='monthly',
                        start_date=random_date + timedelta(days=count*30),
                        end_date=random_date + timedelta(days=count*30),
                        data=self.EXAMPLE_DATA)

        save_yearly_analysis(today.year)

        yearly_analysis = GeneralAnalysisWikilegis.objects.filter(
            period=period)

        assert GeneralAnalysisWikilegis.objects.count() == NUMBER_ANALYSIS + 1
        assert yearly_analysis.count() == 1
        assert yearly_analysis.first(
        ).data['votes'] == self.EXAMPLE_DATA['votes'] * NUMBER_ANALYSIS
        assert yearly_analysis.first(
        ).data['suggestions'] == self.EXAMPLE_DATA['suggestions'] * \
            NUMBER_ANALYSIS

    @pytest.mark.django_db
    def test_save_all_analysis(self):
        NUMBER_DAILY_ANALYSIS = 10
        NUMBER_MONTHLY_ANALYSIS = 5
        NUMBER_YEARLY_ANALYSIS = 1
        period = 'all'
        today = date.today()
        date_last_year = today.year - 1
        date_current_year = date(today.year, 1, 1)

        for count in range(NUMBER_DAILY_ANALYSIS):
            mixer.blend(GeneralAnalysisWikilegis, period='daily',
                        start_date=today.replace(day=count + 1),
                        end_date=today.replace(day=count + 1),
                        data=self.EXAMPLE_DATA)

        for count in range(NUMBER_MONTHLY_ANALYSIS):
            mixer.blend(GeneralAnalysisWikilegis, period='monthly',
                        start_date=date_current_year.replace(month=count + 1),
                        end_date=date_current_year.replace(month=count + 1),
                        data=self.EXAMPLE_DATA)

        mixer.blend(GeneralAnalysisWikilegis, period='yearly',
                    start_date=date(date_last_year, 1, 1),
                    end_date=date(date_last_year, 1, 1),
                    data=self.EXAMPLE_DATA)

        save_all_analysis()

        all_analysis = GeneralAnalysisWikilegis.objects.filter(
            period=period)

        assert GeneralAnalysisWikilegis.objects.count() == (
            NUMBER_DAILY_ANALYSIS + NUMBER_MONTHLY_ANALYSIS +
            NUMBER_YEARLY_ANALYSIS + 1)
        assert all_analysis.count() == 1
        assert all_analysis.first().data['votes'] == (
            NUMBER_DAILY_ANALYSIS + NUMBER_MONTHLY_ANALYSIS +
            NUMBER_YEARLY_ANALYSIS) * self.EXAMPLE_DATA['votes']
        assert all_analysis.first().data['suggestions'] == (
            NUMBER_DAILY_ANALYSIS + NUMBER_MONTHLY_ANALYSIS +
            NUMBER_YEARLY_ANALYSIS) * self.EXAMPLE_DATA['suggestions']

    @pytest.mark.django_db
    def test_task_get_month_analysis(self):
        NUMBER_DAILY_ANALYSIS = 10
        today = date.today()
        last_month = today.replace(
            day=1) - timedelta(days=NUMBER_DAILY_ANALYSIS)
        range_date = calendar.monthrange(last_month.year, last_month.month)
        last_day = range_date[1]
        for count in range(NUMBER_DAILY_ANALYSIS):
            mixer.blend(GeneralAnalysisWikilegis, period='daily',
                        start_date=last_month.replace(day=count + 1),
                        end_date=last_month.replace(day=count + 1),
                        data=self.EXAMPLE_DATA)
        get_month_analysis.apply()

        month_analysis = GeneralAnalysisWikilegis.objects.filter(
            period='monthly').first()

        assert GeneralAnalysisWikilegis.objects.count() == (
            NUMBER_DAILY_ANALYSIS + 1)
        assert month_analysis.start_date == date(
            last_month.year, last_month.month, 1)
        assert month_analysis.end_date == date(
            last_month.year, last_month.month, last_day)
        assert month_analysis.data is not None
        assert month_analysis.data['votes'] == (
            NUMBER_DAILY_ANALYSIS * self.EXAMPLE_DATA['votes'])
        assert month_analysis.data['suggestions'] == (
            NUMBER_DAILY_ANALYSIS * self.EXAMPLE_DATA['suggestions'])

    @pytest.mark.django_db
    def test_task_get_month_analysis_with_args(self):
        NUMBER_DAILY_ANALYSIS = 10
        today = date.today()
        last_month = today.replace(
            day=1) - timedelta(days=NUMBER_DAILY_ANALYSIS)
        range_date = calendar.monthrange(last_month.year, last_month.month)
        last_day = range_date[1]
        for count in range(NUMBER_DAILY_ANALYSIS):
            mixer.blend(GeneralAnalysisWikilegis, period='daily',
                        start_date=last_month.replace(day=count + 1),
                        end_date=last_month.replace(day=count + 1),
                        data=self.EXAMPLE_DATA)
        get_month_analysis.apply(args=[last_month.month, last_month.year])

        month_analysis = GeneralAnalysisWikilegis.objects.filter(
            period='monthly').first()

        assert GeneralAnalysisWikilegis.objects.count() == (
            NUMBER_DAILY_ANALYSIS + 1)
        assert month_analysis.start_date == date(
            last_month.year, last_month.month, 1)
        assert month_analysis.end_date == date(
            last_month.year, last_month.month, last_day)
        assert month_analysis.data is not None
        assert month_analysis.data['votes'] == (
            NUMBER_DAILY_ANALYSIS * self.EXAMPLE_DATA['votes'])
        assert month_analysis.data['suggestions'] == (
            NUMBER_DAILY_ANALYSIS * self.EXAMPLE_DATA['suggestions'])

    @pytest.mark.django_db
    def test_task_get_yearly_analysis(self):
        NUMBER_MONTHLY_ANALYSIS = 12
        today = date.today()
        last_year = today.year - 1
        first_date = date(last_year, 1, 1)
        for count in range(1, NUMBER_MONTHLY_ANALYSIS + 1):
            mixer.blend(GeneralAnalysisWikilegis, period='monthly',
                        start_date=first_date.replace(month=count),
                        end_date=first_date.replace(month=count),
                        data=self.EXAMPLE_DATA)
        get_yearly_analysis.apply()

        month_analysis = GeneralAnalysisWikilegis.objects.filter(
            period='yearly').first()

        assert GeneralAnalysisWikilegis.objects.count() == (
            NUMBER_MONTHLY_ANALYSIS + 1)
        assert month_analysis.start_date == date(last_year, 1, 1)
        assert month_analysis.end_date == date(last_year, 12, 31)
        assert month_analysis.data is not None
        assert month_analysis.data['votes'] == (
            NUMBER_MONTHLY_ANALYSIS * self.EXAMPLE_DATA['votes'])
        assert month_analysis.data['suggestions'] == (
            NUMBER_MONTHLY_ANALYSIS * self.EXAMPLE_DATA['suggestions'])

    @pytest.mark.django_db
    def test_task_get_yearly_analysis_with_args(self):
        NUMBER_MONTHLY_ANALYSIS = 12
        today = date.today()
        first_date = date(today.year, 1, 1)
        for count in range(1, NUMBER_MONTHLY_ANALYSIS + 1):
            mixer.blend(GeneralAnalysisWikilegis, period='monthly',
                        start_date=first_date.replace(month=count),
                        end_date=first_date.replace(month=count),
                        data=self.EXAMPLE_DATA)
        get_yearly_analysis.apply(args=[today.year])

        month_analysis = GeneralAnalysisWikilegis.objects.filter(
            period='yearly').first()

        assert GeneralAnalysisWikilegis.objects.count() == (
            NUMBER_MONTHLY_ANALYSIS + 1)
        assert month_analysis.start_date == date(today.year, 1, 1)
        assert month_analysis.end_date == date(today.year, 12, 31)
        assert month_analysis.data is not None
        assert month_analysis.data['votes'] == (
            NUMBER_MONTHLY_ANALYSIS * self.EXAMPLE_DATA['votes'])
        assert month_analysis.data['suggestions'] == (
            NUMBER_MONTHLY_ANALYSIS * self.EXAMPLE_DATA['suggestions'])

    @pytest.mark.django_db
    def test_task_get_all_analysis(self):
        NUMBER_DAILY_ANALYSIS = 10
        NUMBER_MONTHLY_ANALYSIS = 5
        NUMBER_YEARLY_ANALYSIS = 1
        period = 'all'
        today = date.today()
        date_last_year = today.year - 1
        date_current_year = date(today.year, 1, 1)

        for count in range(NUMBER_DAILY_ANALYSIS):
            mixer.blend(GeneralAnalysisWikilegis, period='daily',
                        start_date=today.replace(day=count + 1),
                        end_date=today.replace(day=count + 1),
                        data=self.EXAMPLE_DATA)

        for count in range(NUMBER_MONTHLY_ANALYSIS):
            mixer.blend(GeneralAnalysisWikilegis, period='monthly',
                        start_date=date_current_year.replace(month=count + 1),
                        end_date=date_current_year.replace(month=count + 1),
                        data=self.EXAMPLE_DATA)

        mixer.blend(GeneralAnalysisWikilegis, period='yearly',
                    start_date=date(date_last_year, 1, 1),
                    end_date=date(date_last_year, 1, 1),
                    data=self.EXAMPLE_DATA)

        get_all_analysis.apply()

        all_analysis = GeneralAnalysisWikilegis.objects.filter(
            period=period)

        assert GeneralAnalysisWikilegis.objects.count() == (
            NUMBER_DAILY_ANALYSIS + NUMBER_MONTHLY_ANALYSIS +
            NUMBER_YEARLY_ANALYSIS + 1)
        assert all_analysis.count() == 1
        assert all_analysis.first().data['votes'] == (
            NUMBER_DAILY_ANALYSIS + NUMBER_MONTHLY_ANALYSIS +
            NUMBER_YEARLY_ANALYSIS) * self.EXAMPLE_DATA['votes']
        assert all_analysis.first().data['suggestions'] == (
            NUMBER_DAILY_ANALYSIS + NUMBER_MONTHLY_ANALYSIS +
            NUMBER_YEARLY_ANALYSIS) * self.EXAMPLE_DATA['suggestions']

    @pytest.mark.django_db
    def test_task_get_all_period_analysis(self):
        NUMBER_DAILY_ANALYSIS = 10
        today = date.today()
        FIRST_YEAR = 2019
        FIRST_MONTH = 1
        LAST_YEAR = today.year
        LAST_MONTH = today.month

        start_date = date(FIRST_YEAR, FIRST_MONTH, 31)
        end_date = date(LAST_YEAR, LAST_MONTH, 1)

        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        for count in range(NUMBER_DAILY_ANALYSIS):
            random_number_of_days = randrange(days_between_dates)
            random_date = start_date + timedelta(days=random_number_of_days)
            mixer.blend(GeneralAnalysisWikilegis, period='daily',
                        start_date=random_date, end_date=random_date)

        get_all_period_analysis.apply()

        daily_analysis = GeneralAnalysisWikilegis.objects.filter(
            period='daily')

        monthly_analysis = GeneralAnalysisWikilegis.objects.filter(
            period='monthly')

        yearly_analysis = GeneralAnalysisWikilegis.objects.filter(
            period='yearly')

        all_analysis = GeneralAnalysisWikilegis.objects.filter(
            period='all')

        assert daily_analysis.count() >= 1
        assert monthly_analysis.count() >= 1
        assert yearly_analysis.count() >= 1
        assert all_analysis.count() == 1
