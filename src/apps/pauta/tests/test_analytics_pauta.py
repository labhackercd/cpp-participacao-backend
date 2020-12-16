import pytest
from mixer.backend.django import mixer
from apps.pauta.models import PautasGA
from django.db import IntegrityError
from apps.pauta.tasks import (get_ga_pautas_daily,
                              get_ga_pautas_monthly,
                              get_ga_pautas_yearly)
from datetime import date, timedelta

DATE_FORMAT = '%Y-%m-%d'


class TestGAPautas:

    def test_apps(self):
        from apps.pauta.apps import PautaConfig
        assert PautaConfig.name == 'Pauta Participativa'

    @pytest.mark.django_db
    def test_pautas_ga_create(self):
        mixer.blend(PautasGA)
        assert PautasGA.objects.count() == 1

    @pytest.mark.django_db
    def test_pautas_ga_error(self):
        content = mixer.blend(PautasGA)
        with pytest.raises(IntegrityError) as excinfo:
            mixer.blend(PautasGA,
                        period=content.period,
                        start_date=content.start_date)
        assert 'duplicate key value violates unique constraint' in str(
            excinfo.value)

    @pytest.mark.django_db
    def test_monthly_get_pautas_ga_data(self):
        json_data = {"date": "00000000", "users": 10, "newUsers": 10,
                     "sessions": 10, "pageViews": 10}

        mixer.cycle(5).blend(PautasGA, period='daily', data=json_data,
                             start_date=mixer.sequence('2020-10-1{0}'),
                             end_date=mixer.sequence('2020-10-1{0}'))

        get_ga_pautas_monthly.apply(args=(['2020-10-01']))

        monthly_data = PautasGA.objects.filter(period='monthly').first()

        assert monthly_data.data['users'] == 50
        assert monthly_data.data['newUsers'] == 50
        assert monthly_data.data['sessions'] == 50
        assert monthly_data.data['pageViews'] == 50

    @pytest.mark.django_db
    def test_monthly_get_pautas_ga_data_without_start_date(self):
        end_date = date.today().replace(day=1) - timedelta(days=1)
        str_date = end_date.strftime(DATE_FORMAT)
        json_data = {"date": "00000000", "users": 10, "newUsers": 10,
                     "sessions": 10, "pageViews": 10}

        mixer.blend(PautasGA, period='daily', data=json_data,
                    start_date=str_date, end_date=str_date)

        get_ga_pautas_monthly.apply()

        monthly_data = PautasGA.objects.filter(period='monthly').first()

        assert monthly_data.data['users'] == 10
        assert monthly_data.data['newUsers'] == 10
        assert monthly_data.data['sessions'] == 10
        assert monthly_data.data['pageViews'] == 10

    @pytest.mark.django_db
    def test_yearly_get_pautas_ga_data(self):
        json_data = {"users": 10, "newUsers": 10,
                     "sessions": 10, "pageViews": 10}
        start_dates = ['2019-01-01', '2019-02-01', '2019-03-01']
        end_dates = ['2019-01-31', '2019-02-28', '2019-03-31']
        for i in range(3):
            mixer.blend(PautasGA, period='monthly', data=json_data,
                        start_date=start_dates[i], end_date=end_dates[i])

        get_ga_pautas_yearly.apply(args=(['2019-01-01']))

        monthly_data = PautasGA.objects.filter(period='yearly').first()

        assert monthly_data.data['users'] == 30
        assert monthly_data.data['newUsers'] == 30
        assert monthly_data.data['sessions'] == 30
        assert monthly_data.data['pageViews'] == 30

    @pytest.mark.django_db
    def test_yearly_get_pautas_ga_data_without_start_date(self):
        json_data = {"users": 10, "newUsers": 10,
                     "sessions": 10, "pageViews": 10}
        end_date = date.today().replace(day=1, month=1) - timedelta(days=1)
        str_date = end_date.strftime(DATE_FORMAT)
        mixer.blend(PautasGA, period='monthly', data=json_data,
                    start_date=str_date, end_date=str_date)

        get_ga_pautas_yearly.apply()

        monthly_data = PautasGA.objects.filter(period='yearly').first()

        assert monthly_data.data['users'] == 10
        assert monthly_data.data['newUsers'] == 10
        assert monthly_data.data['sessions'] == 10
        assert monthly_data.data['pageViews'] == 10

    @pytest.mark.django_db
    def test_get_ga_pautas_daily(self, mocker):
        ga_data = ['20201208', '647', '446', '830', '1692']
        mocker.patch(
            'apps.pauta.tasks.get_analytics_data',
            return_value=[ga_data])
        get_ga_pautas_daily.apply()
        data = {
            "date": ga_data[0],
            "users": ga_data[1],
            "newUsers": ga_data[2],
            "sessions": ga_data[3],
            "pageViews": ga_data[4],
        }

        adiencias_ga = PautasGA.objects.first()

        assert PautasGA.objects.count() > 0
        assert adiencias_ga.data == data
