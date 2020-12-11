import pytest
from apps.wikilegis.models import WikilegisGA
from django.db import IntegrityError
from mixer.backend.django import mixer
from apps.wikilegis.tasks import (get_ga_wikilegis_daily)


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
