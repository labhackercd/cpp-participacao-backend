from utils.data import convert_ga_date, compile_ga_data
from datetime import date


def test_convert_ga_date():
    ga_date_format = '20200101'
    ga_date = convert_ga_date(ga_date_format)

    assert ga_date == date(2020, 1, 1)


def test_compile_ga_data_daily():
    data_daily = ['20201123', '10', '10', '10', '10']
    data, start_date, end_date = compile_ga_data(data_daily, 'daily')

    assert start_date == date(2020, 11, 23)
    assert end_date == date(2020, 11, 23)
    assert data['date'] == '20201123'
    assert data['users'] == '10'
    assert data['newUsers'] == '10'
    assert data['sessions'] == '10'
    assert data['pageViews'] == '10'


def test_compile_ga_data_monthly():
    data_monthly = {
        'month': date(2020, 1, 1),
        'total_users': 10,
        'total_newusers': 10,
        'total_sessions': 10,
        'total_pageviews': 10
    }

    data, start_date, end_date = compile_ga_data(data_monthly, 'monthly')

    assert start_date == date(2020, 1, 1)
    assert end_date == date(2020, 1, 31)
    assert data['users'] == 10
    assert data['newUsers'] == 10
    assert data['sessions'] == 10
    assert data['pageViews'] == 10


def test_compile_ga_data_yearly():
    data_yearly = {
        'year': date(2019, 1, 1),
        'total_users': 10,
        'total_newusers': 10,
        'total_sessions': 10,
        'total_pageviews': 10
    }

    data, start_date, end_date = compile_ga_data(data_yearly, 'yearly')

    assert start_date == date(2019, 1, 1)
    assert end_date == date(2019, 12, 31)
    assert data['users'] == 10
    assert data['newUsers'] == 10
    assert data['sessions'] == 10
    assert data['pageViews'] == 10
