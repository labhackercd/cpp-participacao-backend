import pytest
from apps.audiencias.models import AudienciasGA
from django.db import IntegrityError
from mixer.backend.django import mixer
from datetime import date, timedelta
from apps.audiencias.tasks import (get_ga_audiencias_daily,
                                   get_ga_audiencias_monthly,
                                   get_ga_audiencias_yearly)


class TestGAAudiencias:
    json_monthly = {"date": "00000000", "users": 10, "newUsers": 10,
                    "sessions": 10, "pageViews": 10}
    json_yearly = {"users": 10, "newUsers": 10,
                   "sessions": 10, "pageViews": 10}

    @pytest.mark.django_db
    def test_audiencias_ga_create(self):
        mixer.blend(AudienciasGA)
        assert AudienciasGA.objects.count() == 1

    @pytest.mark.django_db
    def test_audiencias_ga_error(self):
        content = mixer.blend(AudienciasGA)
        with pytest.raises(IntegrityError) as excinfo:
            mixer.blend(AudienciasGA,
                        period=content.period,
                        start_date=content.start_date)
        assert 'duplicate key value violates unique constraint' in str(
            excinfo.value)

    @pytest.mark.django_db
    def test_get_operating_system(self, mocker):
        ga_data = ['20201208', '647', '446', '830', '1692']
        mocker.patch(
            'apps.audiencias.tasks.get_analytics_data',
            return_value=[ga_data])
        get_ga_audiencias_daily.apply()
        data = {
            "date": ga_data[0],
            "users": ga_data[1],
            "newUsers": ga_data[2],
            "sessions": ga_data[3],
            "pageViews": ga_data[4],
        }

        adiencias_ga = AudienciasGA.objects.first()

        assert AudienciasGA.objects.count() > 0
        assert adiencias_ga.data == data

    @pytest.mark.django_db
    def test_monthly_get_pautas_ga_data(self):
        mixer.cycle(5).blend(AudienciasGA, period='daily',
                             data=self.json_monthly,
                             start_date=mixer.sequence('2020-10-1{0}'),
                             end_date=mixer.sequence('2020-10-1{0}'))

        get_ga_audiencias_monthly.apply(args=(['2020-10-01']))

        monthly_data = AudienciasGA.objects.filter(period='monthly').first()

        assert monthly_data.data['users'] == 50
        assert monthly_data.data['newUsers'] == 50
        assert monthly_data.data['sessions'] == 50
        assert monthly_data.data['pageViews'] == 50

    @pytest.mark.django_db
    def test_yearly_get_pautas_ga_data(self):
        start_dates = ['2019-01-01', '2019-02-01', '2019-03-01']
        end_dates = ['2019-01-31', '2019-02-28', '2019-03-31']
        for i in range(3):
            mixer.blend(AudienciasGA, period='monthly', data=self.json_yearly,
                        start_date=start_dates[i], end_date=end_dates[i])

        get_ga_audiencias_yearly.apply(args=(['2019-01-01']))

        monthly_data = AudienciasGA.objects.filter(period='yearly').first()

        assert monthly_data.data['users'] == 30
        assert monthly_data.data['newUsers'] == 30
        assert monthly_data.data['sessions'] == 30
        assert monthly_data.data['pageViews'] == 30

    @pytest.mark.django_db
    def test_monthly_get_pautas_ga_data_without_args(self):
        last_month = date.today().replace(day=1) - timedelta(days=1)
        last_date = str(last_month)[:8]
        mixer.cycle(5).blend(AudienciasGA, period='daily',
                             data=self.json_monthly,
                             start_date=mixer.sequence(last_date+'1{0}'),
                             end_date=mixer.sequence(last_date+'1{0}'))

        get_ga_audiencias_monthly.apply()

        monthly_data = AudienciasGA.objects.filter(period='monthly').first()

        assert monthly_data.data['users'] == 50
        assert monthly_data.data['newUsers'] == 50
        assert monthly_data.data['sessions'] == 50
        assert monthly_data.data['pageViews'] == 50

    @pytest.mark.django_db
    def test_yearly_get_pautas_ga_data_without_args(self):
        start_dates = ['2019-01-01', '2019-02-01', '2019-03-01']
        end_dates = ['2019-01-31', '2019-02-28', '2019-03-31']
        for i in range(3):
            mixer.blend(AudienciasGA, period='monthly', data=self.json_yearly,
                        start_date=start_dates[i], end_date=end_dates[i])

        get_ga_audiencias_yearly.apply()

        monthly_data = AudienciasGA.objects.filter(period='yearly').first()

        assert monthly_data.data['users'] == 30
        assert monthly_data.data['newUsers'] == 30
        assert monthly_data.data['sessions'] == 30
        assert monthly_data.data['pageViews'] == 30
