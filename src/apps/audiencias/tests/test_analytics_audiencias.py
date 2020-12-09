import pytest
from apps.audiencias.models import AudienciasGA
from django.db import IntegrityError
from mixer.backend.django import mixer


class TestGAAudiencias:
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
