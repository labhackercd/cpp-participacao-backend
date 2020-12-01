from datetime import date, datetime, timedelta
import calendar

import pytest
import responses
from random import randrange
from django.conf import settings
from django.db import IntegrityError
from mixer.backend.django import mixer
from apps.audiencias.tests.mock_json import MOCK_JSON_ROOM
from apps.audiencias.models import (
    RoomAnalysisAudiencias, GeneralAnalysisAudiencias)
from apps.audiencias.tasks import (
    create_room, get_rooms, get_or_create_analyse, count_data_analysis,
    save_daily_analysis_room, save_monthly_room_analysis,
    save_yearly_room_analysis, save_all_room_analysis, get_all_room_analysis,
    get_daily_room_analysis, get_monthly_room_analysis,
    get_yearly_room_analysis)


class TestRoomAnalysisAudiencias:
    ROOM_AUDIENCIAS = '/audiencias/api/room/'
    NUMBER_OF_ROOMS_IN_MOCK = 2
    EXAMPLE_DATA = data = {'questions_count': 10,
                           'answered_questions_count': 20,
                           'messages_count': 30,
                           'votes_count': 40,
                           'participants_count': 50,
                           'room_count': 60,
                           }

    def test_name_app_audiencias(self):
        from apps.audiencias.apps import AudienciasConfig
        app = AudienciasConfig

        assert app.name == 'audiencias'

    @pytest.mark.django_db
    def test_create_room_analyse(self):
        room = mixer.blend(RoomAnalysisAudiencias)

        count_room = RoomAnalysisAudiencias.objects.count()
        saved_romm = RoomAnalysisAudiencias.objects.get(id=1)

        assert count_room == 1
        assert saved_romm.data == room.data
        assert saved_romm.room_id == room.room_id
        assert saved_romm.meeting_code == room.meeting_code
        assert saved_romm.period == room.period
        assert saved_romm.start_date == room.start_date
        assert saved_romm.end_date == room.end_date

    @pytest.mark.django_db
    def test_create_room_data_error(self):
        with pytest.raises(AttributeError) as excinfo:
            data = {'error': 'error'}
            create_room(data)
        assert 'Room missing data' in str(excinfo)

    @pytest.mark.django_db
    def test_create_room_meeting_code_empty(self):
        data = {'cod_reunion': '', 'id': 1,
                'date': '2020-11-25T10:00:00'}
        room = create_room(data)
        room_date = date(2020, 11, 25)

        assert room.period == 'daily'
        assert room.room_id == data['id']
        assert room.meeting_code is None
        assert room.start_date == room_date
        assert room.end_date == room_date
        assert room.data == data

    @pytest.mark.django_db
    def test_erro_create_equal_room_analyse(self):
        with pytest.raises(IntegrityError) as excinfo:
            mixer.cycle(2).blend(RoomAnalysisAudiencias, room_id=1)
        assert 'duplicate key value violates unique constraint' in str(excinfo)

    @pytest.mark.django_db
    def test_create_room(self):
        data = {'cod_reunion': 1, 'id': 1, 'date': '2020-11-25T10:00:00'}
        room = create_room(data)
        room_date = date(2020, 11, 25)

        assert room.period == 'daily'
        assert room.room_id == data['id']
        assert room.meeting_code == data['cod_reunion']
        assert room.start_date == room_date
        assert room.end_date == room_date
        assert room.data == data

    @pytest.mark.django_db
    @responses.activate
    def test_task_get_all_rooms(self):
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        url = settings.EDEMOCRACIA_URL + self.ROOM_AUDIENCIAS + \
            '?date__lte={}'.format(yesterday.strftime('%Y-%m-%d'))
        responses.add(responses.GET, url, json=MOCK_JSON_ROOM, status=200)
        get_rooms.apply(args=['all'])

        rooms = RoomAnalysisAudiencias.objects.all()

        assert responses.calls[0].request.url == url
        assert rooms.count() == self.NUMBER_OF_ROOMS_IN_MOCK
        assert rooms.first().room_id == 1679
        assert rooms.first().meeting_code == 60075
        assert rooms.first().start_date == date(2020, 11, 20)
        assert rooms.first().end_date == date(2020, 11, 20)
        assert rooms.first().data is not None

    @pytest.mark.django_db
    @responses.activate
    def test_task_get_today_rooms(self):
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        url = settings.EDEMOCRACIA_URL + self.ROOM_AUDIENCIAS + \
            '?date={}'.format(yesterday.strftime('%Y-%m-%d'))
        responses.add(responses.GET, url, json=MOCK_JSON_ROOM, status=200)
        get_rooms.apply()

        rooms = RoomAnalysisAudiencias.objects.all()

        assert responses.calls[0].request.url == url
        assert rooms.count() == self.NUMBER_OF_ROOMS_IN_MOCK
        assert rooms.first().room_id == 1679
        assert rooms.first().meeting_code == 60075
        assert rooms.first().start_date == date(2020, 11, 20)
        assert rooms.first().end_date == date(2020, 11, 20)
        assert rooms.first().data is not None

    @pytest.mark.django_db
    def test_get_or_create(self):
        start_date = '2020-11-25'
        end_date = '2020-11-25'
        data = {'teste_data': 'teste'}
        period = 'daily'
        get_or_create_analyse(start_date, end_date, data, period)

        analyse = GeneralAnalysisAudiencias.objects.first()

        assert GeneralAnalysisAudiencias.objects.count() == 1
        assert analyse.start_date == date(2020, 11, 25)
        assert analyse.end_date == date(2020, 11, 25)
        assert analyse.data == data
        assert analyse.period == period

    @pytest.mark.django_db
    def test_count_data_room_analysis(self):
        NUMBER_ROOMS = 3
        type_analyse = 'room_analyse'
        mixer.cycle(NUMBER_ROOMS).blend(
            RoomAnalysisAudiencias, data=self.EXAMPLE_DATA)
        rooms = RoomAnalysisAudiencias.objects.all().values('data')
        data = count_data_analysis(rooms, type_analyse)

        assert data['questions_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['questions_count']
        assert data['answered_questions_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['answered_questions_count']
        assert data['messages_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['messages_count']
        assert data['votes_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['votes_count']
        assert data['participants_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['participants_count']
        assert data['room_count'] == NUMBER_ROOMS

    @pytest.mark.django_db
    def test_count_data_general_analysis(self):
        NUMBER_ROOMS = 3
        type_analyse = 'general_analyse'
        mixer.cycle(NUMBER_ROOMS).blend(
            GeneralAnalysisAudiencias, data=self.EXAMPLE_DATA)
        analyse = GeneralAnalysisAudiencias.objects.all().values('data')
        data = count_data_analysis(analyse, type_analyse)

        assert data['questions_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['questions_count']
        assert data['answered_questions_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['answered_questions_count']
        assert data['messages_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['messages_count']
        assert data['votes_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['votes_count']
        assert data['participants_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['participants_count']
        assert data['room_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['room_count']

    @pytest.mark.django_db
    def test_get_or_create_analyse(self):
        start_date = date.today()
        end_date = date.today()
        period = 'daily'

        get_or_create_analyse(start_date, end_date, self.EXAMPLE_DATA, period)

        analyse = GeneralAnalysisAudiencias.objects.first()

        assert GeneralAnalysisAudiencias.objects.count() == 1
        assert analyse.start_date == start_date
        assert analyse.end_date == end_date
        assert analyse.period == period
        assert analyse.data == self.EXAMPLE_DATA

    @pytest.mark.django_db
    def test_get_or_create_analyse_existing_analyse(self):
        start_date = date.today()
        end_date = date.today()
        period = 'daily'
        data = {'test': 'test'}

        mixer.blend(GeneralAnalysisAudiencias, start_date=start_date,
                    end_date=end_date, data=data, period=period)

        get_or_create_analyse(start_date, end_date,
                              self.EXAMPLE_DATA, period)

        general_analyse = GeneralAnalysisAudiencias.objects.first()

        assert GeneralAnalysisAudiencias.objects.count() == 1
        assert general_analyse.start_date == start_date
        assert general_analyse.end_date == end_date
        assert general_analyse.data == self.EXAMPLE_DATA
        assert general_analyse.period == period

    @pytest.mark.django_db
    def test_save_daily_analysis_room(self):
        NUMBER_ROOMS = 3
        date_room = date.today()
        period = 'daily'

        mixer.cycle(NUMBER_ROOMS).blend(
            RoomAnalysisAudiencias, start_date=date_room, end_date=date_room,
            data=self.EXAMPLE_DATA, period=period)

        mixer.blend(GeneralAnalysisAudiencias,
                    start_date=date_room + timedelta(days=1),
                    end_date=date_room + timedelta(days=1),
                    data=self.EXAMPLE_DATA, period=period)

        save_daily_analysis_room(date_room)

        analyse = GeneralAnalysisAudiencias.objects.get(
            start_date=date_room, end_date=date_room)

        assert GeneralAnalysisAudiencias.objects.count() == 2
        assert analyse.start_date == date_room
        assert analyse.end_date == date_room
        assert analyse.period == period
        assert analyse.data['questions_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['questions_count']
        assert analyse.data['answered_questions_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['answered_questions_count']
        assert analyse.data['messages_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['messages_count']
        assert analyse.data['votes_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['votes_count']
        assert analyse.data['participants_count'] == NUMBER_ROOMS * \
            self.EXAMPLE_DATA['participants_count']
        assert analyse.data['room_count'] == NUMBER_ROOMS

    @pytest.mark.django_db
    def test_save_monthly_analysis_room(self):
        DAYLI_ANALYSES = 2
        date_room = date.today().replace(day=1)
        range_date = calendar.monthrange(date_room.year, date_room.month)
        last_day = range_date[1]
        daily_period = 'daily'
        monthly_period = 'monthly'

        for count in range(DAYLI_ANALYSES):
            mixer.blend(GeneralAnalysisAudiencias,
                        start_date=date_room + timedelta(days=count),
                        end_date=date_room + timedelta(days=count),
                        data=self.EXAMPLE_DATA,
                        period=daily_period)

        save_monthly_room_analysis(date_room.month, date_room.year)

        analyse = GeneralAnalysisAudiencias.objects.get(period=monthly_period)

        assert GeneralAnalysisAudiencias.objects.count() == DAYLI_ANALYSES + 1
        assert analyse.start_date == date_room
        assert analyse.end_date == date_room.replace(day=last_day)
        assert analyse.period == monthly_period
        assert analyse.data['questions_count'] == DAYLI_ANALYSES * \
            self.EXAMPLE_DATA['questions_count']
        assert analyse.data['answered_questions_count'] == DAYLI_ANALYSES * \
            self.EXAMPLE_DATA['answered_questions_count']
        assert analyse.data['messages_count'] == DAYLI_ANALYSES * \
            self.EXAMPLE_DATA['messages_count']
        assert analyse.data['votes_count'] == DAYLI_ANALYSES * \
            self.EXAMPLE_DATA['votes_count']
        assert analyse.data['participants_count'] == DAYLI_ANALYSES * \
            self.EXAMPLE_DATA['participants_count']
        assert analyse.data['room_count'] == DAYLI_ANALYSES * \
            self.EXAMPLE_DATA['room_count']

    @pytest.mark.django_db
    def test_save_yearly_analysis_room(self):
        MONTHLY_ANALYSES = 2
        date_room = date.today().replace(day=1)
        start_date = date_room.replace(month=1)
        end_date = date_room.replace(month=12).replace(day=31)
        monthly_period = 'monthly'
        yearly_period = 'yearly'

        for count in range(MONTHLY_ANALYSES):
            mixer.blend(GeneralAnalysisAudiencias,
                        start_date=date_room + timedelta(days=count*30),
                        end_date=date_room + timedelta(days=count*30),
                        data=self.EXAMPLE_DATA,
                        period=monthly_period)

        save_yearly_room_analysis(date_room.year)

        analyse = GeneralAnalysisAudiencias.objects.get(period=yearly_period)

        assert GeneralAnalysisAudiencias.objects.count() == MONTHLY_ANALYSES +\
            1
        assert analyse.start_date == start_date
        assert analyse.end_date == end_date
        assert analyse.period == yearly_period
        assert analyse.data['questions_count'] == MONTHLY_ANALYSES * \
            self.EXAMPLE_DATA['questions_count']
        assert analyse.data['answered_questions_count'] == MONTHLY_ANALYSES * \
            self.EXAMPLE_DATA['answered_questions_count']
        assert analyse.data['messages_count'] == MONTHLY_ANALYSES * \
            self.EXAMPLE_DATA['messages_count']
        assert analyse.data['votes_count'] == MONTHLY_ANALYSES * \
            self.EXAMPLE_DATA['votes_count']
        assert analyse.data['participants_count'] == MONTHLY_ANALYSES * \
            self.EXAMPLE_DATA['participants_count']
        assert analyse.data['room_count'] == MONTHLY_ANALYSES * \
            self.EXAMPLE_DATA['room_count']

    @pytest.mark.django_db
    def test_save_all_analysis_room(self):
        today = date.today()
        YEARLY_ANALYSES = 2
        MONTHLY_ANALYSES = 4
        DAILY_ANALYSES = 3
        ALL_ANALYSES = 1
        FIRST_YEAR = 2015
        start_date = date(FIRST_YEAR, 1, 1)
        end_date = date(FIRST_YEAR, 12, 31)
        yearly_period = 'yearly'
        monthly_period = 'monthly'
        daily_period = 'daily'
        all_period = 'all'

        for count in range(YEARLY_ANALYSES):
            mixer.blend(GeneralAnalysisAudiencias,
                        start_date=start_date.replace(year=FIRST_YEAR + count),
                        end_date=end_date.replace(year=FIRST_YEAR + count),
                        data=self.EXAMPLE_DATA,
                        period=yearly_period)

        for count in range(MONTHLY_ANALYSES):
            mixer.blend(GeneralAnalysisAudiencias,
                        start_date='{}-{}-1'.format(today.year, count + 1),
                        end_date='{}-{}-28'.format(today.year, count + 1),
                        data=self.EXAMPLE_DATA,
                        period=monthly_period)

        for count in range(DAILY_ANALYSES):
            mixer.blend(GeneralAnalysisAudiencias,
                        start_date='{0}-{1}-{2}'.format(
                            today.year, today.month, count + 1),
                        end_date='{0}-{1}-{2}'.format(today.year,
                                                      today.month, count + 1),
                        data=self.EXAMPLE_DATA,
                        period=daily_period)

        save_all_room_analysis()

        analyse = GeneralAnalysisAudiencias.objects.get(period=all_period)

        assert GeneralAnalysisAudiencias.objects.count() == YEARLY_ANALYSES + \
            MONTHLY_ANALYSES + DAILY_ANALYSES + ALL_ANALYSES
        assert analyse.start_date == start_date
        assert analyse.end_date == today - timedelta(days=1)
        assert analyse.period == all_period
        assert analyse.data['questions_count'] == (YEARLY_ANALYSES +
                                                   MONTHLY_ANALYSES +
                                                   DAILY_ANALYSES) * \
            self.EXAMPLE_DATA['questions_count']
        assert analyse.data['answered_questions_count'] == (YEARLY_ANALYSES +
                                                            MONTHLY_ANALYSES +
                                                            DAILY_ANALYSES) * \
            self.EXAMPLE_DATA['answered_questions_count']
        assert analyse.data['messages_count'] == (YEARLY_ANALYSES +
                                                  MONTHLY_ANALYSES +
                                                  DAILY_ANALYSES) * \
            self.EXAMPLE_DATA['messages_count']
        assert analyse.data['votes_count'] == (YEARLY_ANALYSES +
                                               MONTHLY_ANALYSES +
                                               DAILY_ANALYSES) * \
            self.EXAMPLE_DATA['votes_count']
        assert analyse.data['participants_count'] == (YEARLY_ANALYSES +
                                                      MONTHLY_ANALYSES +
                                                      DAILY_ANALYSES) * \
            self.EXAMPLE_DATA['participants_count']
        assert analyse.data['room_count'] == (YEARLY_ANALYSES +
                                              MONTHLY_ANALYSES +
                                              DAILY_ANALYSES) * \
            self.EXAMPLE_DATA['room_count']

    @pytest.mark.django_db
    def test_get_all_room_analysis(self):
        NUMBER_ROOMS = 10
        today = date.today()
        FIRST_YEAR = 2015
        FIRST_MONTH = 1
        LAST_YEAR = today.year
        LAST_MONTH = today.month

        start_date = date(FIRST_YEAR, FIRST_MONTH, 31)
        end_date = date(LAST_YEAR, LAST_MONTH, 1)

        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        for count in range(NUMBER_ROOMS):
            random_number_of_days = randrange(days_between_dates)
            random_date = start_date + timedelta(days=random_number_of_days)
            mixer.blend(RoomAnalysisAudiencias, period='daily',
                        start_date=random_date, end_date=random_date)

        get_all_room_analysis.apply()

        daily_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='daily')

        monthly_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='monthly')

        yearly_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='yearly')

        all_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='all')

        assert daily_analysis.count() > 1
        assert monthly_analysis.count() > 1
        assert yearly_analysis.count() > 1
        assert all_analysis.count() == 1

    @pytest.mark.django_db
    def test_get_daily_room_analysis_withou_date(self):
        yeasterday = date.today() - timedelta(days=1)
        data = self.EXAMPLE_DATA
        data['room_count'] = 1

        mixer.blend(RoomAnalysisAudiencias, start_date=yeasterday,
                    end_date=yeasterday,
                    data=data, period='daily')

        get_daily_room_analysis.apply()

        daily_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='daily', start_date=yeasterday).first()

        assert GeneralAnalysisAudiencias.objects.count() == 1
        assert daily_analysis.start_date == yeasterday
        assert daily_analysis.end_date == yeasterday
        assert daily_analysis.period == 'daily'
        assert daily_analysis.data == data

    @pytest.mark.django_db
    def test_get_daily_room_analysis_with_date(self):
        example_date = date.today() - timedelta(days=7)
        data = self.EXAMPLE_DATA
        data['room_count'] = 1

        mixer.blend(RoomAnalysisAudiencias, start_date=example_date,
                    end_date=example_date,
                    data=data, period='daily')

        get_daily_room_analysis.apply(args=[example_date])

        daily_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='daily').first()

        assert GeneralAnalysisAudiencias.objects.count() == 1
        assert daily_analysis.start_date == example_date
        assert daily_analysis.end_date == example_date
        assert daily_analysis.period == 'daily'
        assert daily_analysis.data == data

    @pytest.mark.django_db
    def test_get_monthly_room_analysis_without_date(self):
        today = date.today()
        last_month = today.month - 1
        range_date = calendar.monthrange(today.year, last_month)
        last_day = range_date[1]
        start_date = date(today.year, last_month, 1)
        end_date = date(today.year, last_month, last_day)

        mixer.blend(GeneralAnalysisAudiencias, start_date=start_date,
                    end_date=start_date,
                    data=self.EXAMPLE_DATA, period='daily')

        get_monthly_room_analysis.apply()

        monthly_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='monthly').first()

        assert GeneralAnalysisAudiencias.objects.count() == 2
        assert monthly_analysis.start_date == start_date
        assert monthly_analysis.end_date == end_date
        assert monthly_analysis.period == 'monthly'
        assert monthly_analysis.data == self.EXAMPLE_DATA

    @pytest.mark.django_db
    def test_get_monthly_room_analysis_with_date(self):
        today = date.today()
        last_month = today.month - 1
        range_date = calendar.monthrange(today.year, last_month)
        last_day = range_date[1]
        start_date = date(today.year, last_month, 1)
        end_date = date(today.year, last_month, last_day)

        mixer.blend(GeneralAnalysisAudiencias, start_date=start_date,
                    end_date=start_date,
                    data=self.EXAMPLE_DATA, period='daily')

        get_monthly_room_analysis.apply(args=[last_month, today.year])

        monthly_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='monthly').first()

        assert GeneralAnalysisAudiencias.objects.count() == 2
        assert monthly_analysis.start_date == start_date
        assert monthly_analysis.end_date == end_date
        assert monthly_analysis.period == 'monthly'
        assert monthly_analysis.data == self.EXAMPLE_DATA

    @pytest.mark.django_db
    def test_get_yearly_room_analysis_without_date(self):
        FIRST_DAY = 1
        LAST_DAY = 31
        FIRST_MONTH = 1
        LAST_MONTH = 12
        LAST_YEAR = date.today().year - 1
        start_date = date(LAST_YEAR, FIRST_MONTH, FIRST_DAY)
        end_date = date(LAST_YEAR, LAST_MONTH, LAST_DAY)

        mixer.blend(GeneralAnalysisAudiencias, start_date=start_date,
                    end_date=start_date,
                    data=self.EXAMPLE_DATA, period='monthly')

        get_yearly_room_analysis.apply()

        monthly_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='yearly').first()

        assert GeneralAnalysisAudiencias.objects.count() == 2
        assert monthly_analysis.start_date == start_date
        assert monthly_analysis.end_date == end_date
        assert monthly_analysis.period == 'yearly'
        assert monthly_analysis.data == self.EXAMPLE_DATA

    @pytest.mark.django_db
    def test_get_yearly_room_analysis_with_date(self):
        FIRST_DAY = 1
        LAST_DAY = 31
        FIRST_MONTH = 1
        LAST_MONTH = 12
        YEAR = 2019
        start_date = date(YEAR, FIRST_MONTH, FIRST_DAY)
        end_date = date(YEAR, LAST_MONTH, LAST_DAY)

        mixer.blend(GeneralAnalysisAudiencias, start_date=start_date,
                    end_date=start_date,
                    data=self.EXAMPLE_DATA, period='monthly')

        get_yearly_room_analysis.apply(args=[YEAR])

        monthly_analysis = GeneralAnalysisAudiencias.objects.filter(
            period='yearly').first()

        assert GeneralAnalysisAudiencias.objects.count() == 2
        assert monthly_analysis.start_date == start_date
        assert monthly_analysis.end_date == end_date
        assert monthly_analysis.period == 'yearly'
        assert monthly_analysis.data == self.EXAMPLE_DATA
