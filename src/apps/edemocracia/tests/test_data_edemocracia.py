import pytest
from mixer.backend.django import mixer
from apps.edemocracia.models import EdemocraciaAnalysis
from django.db import IntegrityError
from apps.edemocracia.tasks import (save_registers_count,
                                    get_edemocracia_registers_daily,
                                    get_edemocracia_registers_monthly,
                                    get_edemocracia_registers_yearly)
from datetime import date
import responses
from django.conf import settings


class TestAnalysisEdemocracia():
    def test_apps(self):
        from apps.edemocracia.apps import EdemocraciaConfig
        assert EdemocraciaConfig.name == 'eDemocracia'

    @pytest.mark.django_db
    def test_edemocracia_analysis_create(self):
        mixer.blend(EdemocraciaAnalysis)
        assert EdemocraciaAnalysis.objects.count() == 1

    @pytest.mark.django_db
    def test_edemocracia_analysis_integrity_error(self):
        content = mixer.blend(EdemocraciaAnalysis)
        with pytest.raises(IntegrityError) as excinfo:
            mixer.blend(EdemocraciaAnalysis,
                        period=content.period,
                        start_date=content.start_date)
        assert 'duplicate key value violates unique constraint' in str(
            excinfo.value)

    def test_save_registers_daily(self):
        data_daily = ['2020-11-23', 10]
        edem_object = save_registers_count(data_daily, 'daily')

        assert edem_object.period == 'daily'
        assert edem_object.start_date == '2020-11-23'
        assert edem_object.end_date == '2020-11-23'
        assert edem_object.data['register_count'] == 10

    def test_save_registers_monthly(self):
        data_monthly = {
            'month': date(2020, 1, 1),
            'total_registers': 10
        }

        edem_object = save_registers_count(data_monthly, 'monthly')

        assert edem_object.period == 'monthly'
        assert edem_object.start_date == date(2020, 1, 1)
        assert edem_object.end_date == date(2020, 1, 31)
        assert edem_object.data['register_count'] == 10

    def test_save_registers_yearly(self):
        data_yearly = {
            'year': date(2019, 1, 1),
            'total_registers': 10
        }

        edem_object = save_registers_count(data_yearly, 'yearly')

        assert edem_object.period == 'yearly'
        assert edem_object.start_date == date(2019, 1, 1)
        assert edem_object.end_date == date(2019, 12, 31)
        assert edem_object.data['register_count'] == 10

    @pytest.mark.django_db
    @responses.activate
    def test_get_edemocracia_registers_daily(self):
        test_date = '2020-11-23'
        url = (settings.EDEMOCRACIA_URL
               + '/api/v1/user/?date_joined__gte='
               + test_date)
        json_response = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "username": "user1",
                    "first_name": "Joao",
                    "last_name": "",
                    "last_login": "2020-11-23T08:16:38.612651-03:00",
                    "date_joined": "2020-11-23T08:16:37.361042-03:00",
                    "profile": {
                        "id": 1,
                        "gender": None,
                        "uf": None,
                        "country": None,
                        "birthdate": None,
                        "avatar": None
                    }
                },
                {
                    "id": 2,
                    "username": "user2",
                    "first_name": "Paulo",
                    "last_name": "",
                    "last_login": "2020-11-23T08:16:38.612651-03:00",
                    "date_joined": "2020-11-23T08:16:37.361042-03:00",
                    "profile": {
                        "id": 2,
                        "gender": None,
                        "uf": None,
                        "country": None,
                        "birthdate": None,
                        "avatar": None
                    }
                }
            ]
        }

        responses.add(responses.GET, url, json=json_response, status=200)
        get_edemocracia_registers_daily.apply(args=([test_date]))

        daily_data = EdemocraciaAnalysis.objects.filter(
            period='daily', start_date=test_date, end_date=test_date).first()

        assert responses.calls[0].request.url == url
        assert daily_data.period == 'daily'
        assert daily_data.start_date == date(2020, 11, 23)
        assert daily_data.end_date == date(2020, 11, 23)
        assert daily_data.data['register_count'] == 2

    @pytest.mark.django_db
    def test_get_edemocracia_registers_monthly(self):
        json_data = {"register_count": 10}

        mixer.cycle(5).blend(EdemocraciaAnalysis, period='daily',
                             data=json_data, start_date=mixer.sequence(
                                 '2020-10-1{0}'),
                             end_date=mixer.sequence('2020-10-1{0}'))

        get_edemocracia_registers_monthly.apply(args=(['2020-10-01']))

        monthly_data = EdemocraciaAnalysis.objects.filter(
            period='monthly').first()

        assert monthly_data.start_date == date(2020, 10, 1)
        assert monthly_data.end_date == date(2020, 10, 31)
        assert monthly_data.period == 'monthly'
        assert monthly_data.data['register_count'] == 50

    @pytest.mark.django_db
    def test_get_edemocracia_registers_yearly(self):
        json_data = {"register_count": 10}
        start_dates = ['2019-01-01', '2019-02-01', '2019-03-01']
        end_dates = ['2019-01-31', '2019-02-28', '2019-03-31']
        for i in range(3):
            mixer.blend(EdemocraciaAnalysis, period='monthly', data=json_data,
                        start_date=start_dates[i], end_date=end_dates[i])

        get_edemocracia_registers_yearly.apply(args=(['2019-01-01']))

        monthly_data = EdemocraciaAnalysis.objects.filter(
            period='yearly').first()

        assert monthly_data.start_date == date(2019, 1, 1)
        assert monthly_data.end_date == date(2019, 12, 31)
        assert monthly_data.period == 'yearly'
        assert monthly_data.data['register_count'] == 30
