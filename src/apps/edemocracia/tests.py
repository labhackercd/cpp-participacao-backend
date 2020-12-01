import pytest
from mixer.backend.django import mixer
from apps.edemocracia.models import EdemocraciaGA, EdemocraciaAnalysis
from django.db import IntegrityError
from apps.edemocracia.tasks import (get_ga_edemocracia_monthly,
                                    get_ga_edemocracia_yearly,
                                    convert_ga_date,
                                    compile_ga_data,
                                    save_registers_count,
                                    get_edemocracia_registers_daily,
                                    get_edemocracia_registers_monthly,
                                    get_edemocracia_registers_yearly)
from datetime import date
import responses
from django.conf import settings


def test_apps():
    from apps.edemocracia.apps import EdemocraciaConfig
    assert EdemocraciaConfig.name == 'eDemocracia'


@pytest.mark.django_db
def test_edemocracia_analysis_create():
    mixer.blend(EdemocraciaAnalysis)
    assert EdemocraciaAnalysis.objects.count() == 1


@pytest.mark.django_db
def test_edemocracia_analysis_integrity_error():
    content = mixer.blend(EdemocraciaAnalysis)
    with pytest.raises(IntegrityError) as excinfo:
        mixer.blend(EdemocraciaAnalysis,
                    period=content.period,
                    start_date=content.start_date)
    assert 'duplicate key value violates unique constraint' in str(
        excinfo.value)


@pytest.mark.django_db
def test_edemocracia_ga_create():
    mixer.blend(EdemocraciaGA)
    assert EdemocraciaGA.objects.count() == 1


@pytest.mark.django_db
def test_edemocracia_ga_integrity_error():
    content = mixer.blend(EdemocraciaGA)
    with pytest.raises(IntegrityError) as excinfo:
        mixer.blend(EdemocraciaGA,
                    period=content.period,
                    start_date=content.start_date)
    assert 'duplicate key value violates unique constraint' in str(
        excinfo.value)


@pytest.mark.django_db
def test_monthly_get_ga_data():
    json_data = {"date": "00000000", "users": 10, "newUsers": 10,
                 "sessions": 10, "pageViews": 10}

    mixer.cycle(5).blend(EdemocraciaGA, period='daily', data=json_data,
                         start_date=mixer.sequence('2020-10-1{0}'),
                         end_date=mixer.sequence('2020-10-1{0}'))

    get_ga_edemocracia_monthly.apply(args=(['2020-10-01']))

    monthly_data = EdemocraciaGA.objects.filter(period='monthly').first()

    assert monthly_data.data['users'] == 50
    assert monthly_data.data['newUsers'] == 50
    assert monthly_data.data['sessions'] == 50
    assert monthly_data.data['pageViews'] == 50


@pytest.mark.django_db
def test_yearly_get_ga_data():
    json_data = {"users": 10, "newUsers": 10, "sessions": 10, "pageViews": 10}
    start_dates = ['2019-01-01', '2019-02-01', '2019-03-01']
    end_dates = ['2019-01-31', '2019-02-28', '2019-03-31']
    for i in range(3):
        mixer.blend(EdemocraciaGA, period='monthly', data=json_data,
                    start_date=start_dates[i], end_date=end_dates[i])

    get_ga_edemocracia_yearly.apply(args=(['2019-01-01']))

    monthly_data = EdemocraciaGA.objects.filter(period='yearly').first()

    assert monthly_data.data['users'] == 30
    assert monthly_data.data['newUsers'] == 30
    assert monthly_data.data['sessions'] == 30
    assert monthly_data.data['pageViews'] == 30


def test_convert_ga_date():
    ga_date_format = '20200101'
    ga_date = convert_ga_date(ga_date_format)

    assert ga_date == date(2020, 1, 1)


def test_compile_ga_data_daily():
    data_daily = ['20201123', '10', '10', '10', '10']
    ga_object = compile_ga_data(data_daily, 'daily')

    assert ga_object.period == 'daily'
    assert ga_object.start_date == date(2020, 11, 23)
    assert ga_object.end_date == date(2020, 11, 23)
    assert ga_object.data['date'] == '20201123'
    assert ga_object.data['users'] == '10'
    assert ga_object.data['newUsers'] == '10'
    assert ga_object.data['sessions'] == '10'
    assert ga_object.data['pageViews'] == '10'


def test_compile_ga_data_monthly():
    data_monthly = {
        'month': date(2020, 1, 1),
        'total_users': 10,
        'total_newusers': 10,
        'total_sessions': 10,
        'total_pageviews': 10
    }

    ga_object = compile_ga_data(data_monthly, 'monthly')

    assert ga_object.period == 'monthly'
    assert ga_object.start_date == date(2020, 1, 1)
    assert ga_object.end_date == date(2020, 1, 31)
    assert ga_object.data['users'] == 10
    assert ga_object.data['newUsers'] == 10
    assert ga_object.data['sessions'] == 10
    assert ga_object.data['pageViews'] == 10


def test_compile_ga_data_yearly():
    data_yearly = {
        'year': date(2019, 1, 1),
        'total_users': 10,
        'total_newusers': 10,
        'total_sessions': 10,
        'total_pageviews': 10
    }

    ga_object = compile_ga_data(data_yearly, 'yearly')

    assert ga_object.period == 'yearly'
    assert ga_object.start_date == date(2019, 1, 1)
    assert ga_object.end_date == date(2019, 12, 31)
    assert ga_object.data['users'] == 10
    assert ga_object.data['newUsers'] == 10
    assert ga_object.data['sessions'] == 10
    assert ga_object.data['pageViews'] == 10


def test_save_registers_daily():
    data_daily = ['2020-11-23', 10]
    edem_object = save_registers_count(data_daily, 'daily')

    assert edem_object.period == 'daily'
    assert edem_object.start_date == '2020-11-23'
    assert edem_object.end_date == '2020-11-23'
    assert edem_object.data['register_count'] == 10


def test_save_registers_monthly():
    data_monthly = {
        'month': date(2020, 1, 1),
        'total_registers': 10
    }

    edem_object = save_registers_count(data_monthly, 'monthly')

    assert edem_object.period == 'monthly'
    assert edem_object.start_date == date(2020, 1, 1)
    assert edem_object.end_date == date(2020, 1, 31)
    assert edem_object.data['register_count'] == 10


def test_save_registers_yearly():
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
def test_get_edemocracia_registers_daily():
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

    daily_data = EdemocraciaAnalysis.objects.filter(period='daily',
                                                    start_date=test_date,
                                                    end_date=test_date).first()

    assert responses.calls[0].request.url == url
    assert daily_data.period == 'daily'
    assert daily_data.start_date == date(2020, 11, 23)
    assert daily_data.end_date == date(2020, 11, 23)
    assert daily_data.data['register_count'] == 2


@pytest.mark.django_db
def test_get_edemocracia_registers_monthly():
    json_data = {"register_count": 10}

    mixer.cycle(5).blend(EdemocraciaAnalysis, period='daily', data=json_data,
                         start_date=mixer.sequence('2020-10-1{0}'),
                         end_date=mixer.sequence('2020-10-1{0}'))

    get_edemocracia_registers_monthly.apply(args=(['2020-10-01']))

    monthly_data = EdemocraciaAnalysis.objects.filter(period='monthly').first()

    assert monthly_data.start_date == date(2020, 10, 1)
    assert monthly_data.end_date == date(2020, 10, 31)
    assert monthly_data.period == 'monthly'
    assert monthly_data.data['register_count'] == 50


@pytest.mark.django_db
def test_get_edemocracia_registers_yearly():
    json_data = {"register_count": 10}
    start_dates = ['2019-01-01', '2019-02-01', '2019-03-01']
    end_dates = ['2019-01-31', '2019-02-28', '2019-03-31']
    for i in range(3):
        mixer.blend(EdemocraciaAnalysis, period='monthly', data=json_data,
                    start_date=start_dates[i], end_date=end_dates[i])

    get_edemocracia_registers_yearly.apply(args=(['2019-01-01']))

    monthly_data = EdemocraciaAnalysis.objects.filter(period='yearly').first()

    assert monthly_data.start_date == date(2019, 1, 1)
    assert monthly_data.end_date == date(2019, 12, 31)
    assert monthly_data.period == 'yearly'
    assert monthly_data.data['register_count'] == 30
