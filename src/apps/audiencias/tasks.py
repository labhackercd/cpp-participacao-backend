from participacao.celery import app
from .scraping import api_get_rooms
from apps.audiencias.models import (RoomAnalysisAudiencias,
                                    GeneralAnalysisAudiencias)
from datetime import date, timedelta, datetime
import calendar
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Cast, Coalesce
from django.db.models import Func, F, IntegerField, Sum
from django.db.models.expressions import Value


FIRST_YEAR = 2015
FIRST_MONTH = 1
LAST_MONTH = 12
FIRST_DAY = 1
LAST_DAY = 31
DATA_FORMAT = '{0}-{1}-{2}'


@app.task(name="get_rooms")
def get_rooms(periods=None):
    if periods is None:
        periods = 'today'
    rooms = api_get_rooms(periods)
    batch_size = 100

    room_alaysis = [create_room(data) for data in rooms]

    RoomAnalysisAudiencias.objects.bulk_create(
        room_alaysis, batch_size, ignore_conflicts=True)


def create_room(data):
    period = 'daily'
    meeting_code = data.get('cod_reunion', None)
    date_room = data.get('date', None)
    room_id = data.get('id', None)

    if date_room is None or room_id is None:
        raise AttributeError('Room missing data')

    if meeting_code == '':
        meeting_code = None
    str_date = datetime.strptime(date_room, '%Y-%m-%dT%H:%M:%S')

    room_object = RoomAnalysisAudiencias(data=data, room_id=room_id,
                                         start_date=str_date.date(),
                                         end_date=str_date.date(),
                                         period=period,
                                         meeting_code=meeting_code)

    return room_object


@app.task(name='get_all_room_analysis')
def get_all_room_analysis():
    today = date.today()
    LAST_YEAR = today.year
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        if year == LAST_YEAR:
            LAST_MONTH = today.month
        else:
            LAST_MONTH = 12
        for month in range(FIRST_MONTH, LAST_MONTH + 1):
            last_day = 0
            if year == LAST_YEAR and month == today.month:
                last_day = today.day - 1
            else:
                range_date = calendar.monthrange(year, month)
                last_day = range_date[1]
            for day in range(FIRST_DAY, last_day + 1):
                date_analyse = DATA_FORMAT.format(year, month, day)
                save_daily_analysis_room(date_analyse)
            if year == today.year and month == today.month:
                break
            save_monthly_room_analysis(month, year)
        if year < today.year:
            save_yearly_room_analysis(year)
    save_all_room_analysis()


@app.task(name='get_daily_room_analysis')
def get_daily_room_analysis(date_analyse=None):
    if date_analyse is None:
        date_analyse = date.today() - timedelta(days=1)
    save_daily_analysis_room(date_analyse)


@app.task(name='get_monthly_room_analysis')
def get_monthly_room_analysis(month=None, year=None):
    if month is None:
        today = date.today()
        month = today.month - 1
    if year is None:
        today = date.today()
        year = today.year

    save_monthly_room_analysis(month, year)


@app.task(name='get_yearly_room_analysis')
def get_yearly_room_analysis(year=None):
    if year is None:
        today = date.today()
        year = today.year - 1

    save_yearly_room_analysis(year)


def count_data_analysis(analysis, type_analyse):
    room_count = Cast(Func(F('data'), Value('room_count'),
                           function='jsonb_extract_path_text'), IntegerField())
    questions_count = Cast(Func(F('data'), Value('questions_count'),
                                function='jsonb_extract_path_text'),
                           IntegerField())
    answered_questions_count = Cast(Func(F('data'),
                                         Value('answered_questions_count'),
                                         function='jsonb_extract_path_text'),
                                    IntegerField())
    messages_count = Cast(Func(F('data'), Value('messages_count'),
                               function='jsonb_extract_path_text'),
                          IntegerField())
    votes_count = Cast(Func(F('data'), Value('votes_count'),
                            function='jsonb_extract_path_text'),
                       IntegerField())
    participants_count = Cast(Func(F('data'), Value('participants_count'),
                                   function='jsonb_extract_path_text'),
                              IntegerField())

    data = analysis.aggregate(
        questions_count=Coalesce(Sum(questions_count), 0),
        answered_questions_count=Coalesce(Sum(answered_questions_count), 0),
        messages_count=Coalesce(Sum(messages_count), 0),
        votes_count=Coalesce(Sum(votes_count), 0),
        participants_count=Coalesce(Sum(participants_count), 0),
    )

    if type_analyse == 'room_analyse':
        room_count = analysis.count()
    else:
        room_count = analysis.aggregate(
            room_count=Coalesce(Sum(room_count), 0))['room_count']

    data['room_count'] = room_count

    return data


def get_or_create_analyse(start_date, end_date, data, period):
    try:
        analyse = GeneralAnalysisAudiencias.objects.get(
            start_date=start_date, end_date=end_date, period=period)
        analyse.data = data
        analyse.save()
    except ObjectDoesNotExist:
        GeneralAnalysisAudiencias.objects.create(
            start_date=start_date, data=data, end_date=end_date, period=period)


def save_daily_analysis_room(start_date):
    period = 'daily'
    type_analyse = 'room_analyse'

    rooms = RoomAnalysisAudiencias.objects.filter(
        start_date=start_date, end_date=start_date,
        period=period).values('data')
    if rooms.count() > 0:
        data_rooms = rooms
        data = count_data_analysis(data_rooms, type_analyse)
        get_or_create_analyse(start_date, start_date, data, period)


def save_monthly_room_analysis(month, year):
    period = 'monthly'
    minimal_period = 'daily'
    type_analyse = 'general_analyse'

    month_analysis = GeneralAnalysisAudiencias.objects.filter(
        period=minimal_period, start_date__month=month, start_date__year=year,
        end_date__month=month, end_date__year=year).values('data')
    if month_analysis.count() > 0:
        range_date = calendar.monthrange(year, month)
        last_day = range_date[1]
        start_date = DATA_FORMAT.format(year, month, FIRST_DAY)
        end_date = DATA_FORMAT.format(year, month, last_day)
        data = count_data_analysis(month_analysis, type_analyse)

        get_or_create_analyse(start_date, end_date, data, period)


def save_yearly_room_analysis(year):
    period = 'yearly'
    minimal_period = 'monthly'
    type_analyse = 'general_analyse'

    year_analysis = GeneralAnalysisAudiencias.objects.filter(
        period=minimal_period, start_date__year=year,
        end_date__year=year).values('data')
    if year_analysis.count() > 0:
        start_date = DATA_FORMAT.format(year, FIRST_MONTH, FIRST_DAY)
        end_date = DATA_FORMAT.format(year, LAST_MONTH, LAST_DAY)
        data = count_data_analysis(year_analysis, type_analyse)

        get_or_create_analyse(start_date, end_date, data, period)


def save_all_room_analysis():
    daily_period = 'daily'
    monthly_period = 'monthly'
    yearly_period = 'yearly'
    period = 'all'

    type_analyse = 'general_analyse'
    today = date.today()
    end_date = today - timedelta(days=1)

    year_analysis = GeneralAnalysisAudiencias.objects.filter(
        period=yearly_period)
    month_analysis = GeneralAnalysisAudiencias.objects.filter(
        period=monthly_period, start_date__year=today.year,
        end_date__year=today.year)
    daily_analysis = GeneralAnalysisAudiencias.objects.filter(
        period=daily_period, start_date__year=today.year,
        start_date__month=today.month, end_date__year=today.year,
        end_date__month=today.month)
    start_date = DATA_FORMAT.format(FIRST_YEAR, FIRST_MONTH, FIRST_DAY)

    all_analysis = year_analysis | month_analysis | daily_analysis

    data = count_data_analysis(all_analysis, type_analyse)

    get_or_create_analyse(start_date, end_date, data, period)
