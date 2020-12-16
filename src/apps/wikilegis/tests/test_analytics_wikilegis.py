import pytest
from apps.wikilegis.models import WikilegisGA
from django.db import IntegrityError
from mixer.backend.django import mixer
from apps.wikilegis.tasks import (
    get_ga_wikilegis_daily, get_ga_wikilegis_monthly, get_ga_wikilegis_yearly)


class TestGAWikilegis:
    @pytest.mark.django_db
    def test_wikilegis_ga_create(self):
        mixer.blend(WikilegisGA)
        assert WikilegisGA.objects.count() == 1

    @pytest.mark.django_db
    def test_wikilegis_ga_error(self):
        content = mixer.blend(WikilegisGA)
        with pytest.raises(IntegrityError) as excinfo:
            mixer.blend(WikilegisGA,
                        period=content.period,
                        start_date=content.start_date)
        assert 'duplicate key value violates unique constraint' in str(
            excinfo.value)

    @pytest.mark.django_db
    def test_get_ga_wikilegis_daily(self, mocker):
        ga_data = ['20201208', '647', '446', '830', '1692']
        mocker.patch(
            'apps.wikilegis.tasks.get_analytics_data',
            return_value=[ga_data])
        get_ga_wikilegis_daily.apply()
        data = {
            "date": ga_data[0],
            "users": ga_data[1],
            "newUsers": ga_data[2],
            "sessions": ga_data[3],
            "pageViews": ga_data[4],
        }

        adiencias_ga = WikilegisGA.objects.first()

        assert WikilegisGA.objects.count() > 0
        assert adiencias_ga.data == data

    @pytest.mark.django_db
    def test_monthly_get_wikilegis_ga_data(self):
        json_data = {"date": "00000000", "users": 10, "newUsers": 10,
                     "sessions": 10, "pageViews": 10}

        mixer.cycle(5).blend(WikilegisGA, period='daily', data=json_data,
                             start_date=mixer.sequence('2020-10-1{0}'),
                             end_date=mixer.sequence('2020-10-1{0}'))

        get_ga_wikilegis_monthly.apply(args=(['2020-10-01']))

        monthly_data = WikilegisGA.objects.filter(period='monthly').first()

        assert monthly_data.data['users'] == 50
        assert monthly_data.data['newUsers'] == 50
        assert monthly_data.data['sessions'] == 50
        assert monthly_data.data['pageViews'] == 50

    @pytest.mark.django_db
    def test_yearly_get_wikilegis_ga_data(self):
        json_data = {"users": 10, "newUsers": 10,
                     "sessions": 10, "pageViews": 10}
        start_dates = ['2019-01-01', '2019-02-01', '2019-03-01']
        end_dates = ['2019-01-31', '2019-02-28', '2019-03-31']
        for i in range(3):
            mixer.blend(WikilegisGA, period='monthly', data=json_data,
                        start_date=start_dates[i], end_date=end_dates[i])

        get_ga_wikilegis_yearly.apply(args=(['2019-01-01']))

        monthly_data = WikilegisGA.objects.filter(period='yearly').first()

        assert monthly_data.data['users'] == 30
        assert monthly_data.data['newUsers'] == 30
        assert monthly_data.data['sessions'] == 30
        assert monthly_data.data['pageViews'] == 30
