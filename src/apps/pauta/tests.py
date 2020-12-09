import pytest
from mixer.backend.django import mixer
from apps.pauta.models import PautasGA
from django.db import IntegrityError
from apps.pauta.tasks import (get_ga_pautas_monthly,
                              get_ga_pautas_yearly)


def test_apps():
    from apps.pauta.apps import PautaConfig
    assert PautaConfig.name == 'Pauta Participativa'


@pytest.mark.django_db
def test_pautas_ga_create():
    mixer.blend(PautasGA)
    assert PautasGA.objects.count() == 1


@pytest.mark.django_db
def test_pautas_ga_error():
    content = mixer.blend(PautasGA)
    with pytest.raises(IntegrityError) as excinfo:
        mixer.blend(PautasGA,
                    period=content.period,
                    start_date=content.start_date)
    assert 'duplicate key value violates unique constraint' in str(
        excinfo.value)


@pytest.mark.django_db
def test_monthly_get_pautas_ga_data():
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
def test_yearly_get_pautas_ga_data():
    json_data = {"users": 10, "newUsers": 10, "sessions": 10, "pageViews": 10}
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
