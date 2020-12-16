import pytest
from mixer.backend.django import mixer
from apps.pauta.models import PautasVotesAnalysis
from django.db import IntegrityError
from apps.pauta.tasks import (save_votes_count,
                              get_pautas_votes_daily)
from datetime import date, timedelta
import responses
from django.conf import settings
from apps.pauta.tests.mock_json import MOCK_JSON_VOTES, MOCK_JSON_NO_VOTES


class TestPautasVotesAnalysis():
    @pytest.mark.django_db
    def test_pauta_votes_analysis_create(self):
        mixer.blend(PautasVotesAnalysis)
        assert PautasVotesAnalysis.objects.count() == 1

    @pytest.mark.django_db
    def test_pauta_votes_analysis_integrity_error(self):
        content = mixer.blend(PautasVotesAnalysis)
        with pytest.raises(IntegrityError) as excinfo:
            mixer.blend(PautasVotesAnalysis,
                        period=content.period,
                        start_date=content.start_date)
        assert 'duplicate key value violates unique constraint' in str(
            excinfo.value)

    def test_save_votes_count_daily(self):
        data_daily = ['2020-11-23', 10]
        pauta_votes_object = save_votes_count(data_daily, 'daily')

        assert pauta_votes_object.period == 'daily'
        assert pauta_votes_object.start_date == '2020-11-23'
        assert pauta_votes_object.end_date == '2020-11-23'
        assert pauta_votes_object.data['votes_count'] == 10

    @pytest.mark.django_db
    @responses.activate
    def test_get_pauta_votes_daily(self):
        test_date = '2019-11-22'
        url = (settings.EDEMOCRACIA_URL
               + '/pautaparticipativa/api/v1/vote/?datetime__gte='
               + test_date)
        json_response = MOCK_JSON_VOTES

        responses.add(responses.GET, url, json=json_response, status=200)
        get_pautas_votes_daily.apply(args=([test_date]))

        daily_data = PautasVotesAnalysis.objects.filter(
            period='daily', start_date=test_date, end_date=test_date).first()

        assert responses.calls[0].request.url == url
        assert daily_data.period == 'daily'
        assert daily_data.start_date == date(2019, 11, 22)
        assert daily_data.end_date == date(2019, 11, 22)
        assert daily_data.data['votes_count'] == 1

    @pytest.mark.django_db
    @responses.activate
    def test_get_pauta_votes_daily_without_start_date(self):
        yesterday = date.today() - timedelta(days=1)
        url = (settings.EDEMOCRACIA_URL
               + '/pautaparticipativa/api/v1/vote/?datetime__gte='
               + yesterday.strftime('%Y-%m-%d'))
        json_response = MOCK_JSON_NO_VOTES

        responses.add(responses.GET, url, json=json_response, status=200)
        get_pautas_votes_daily.apply()

        assert responses.calls[0].request.url == url
        assert PautasVotesAnalysis.objects.count() == 0
