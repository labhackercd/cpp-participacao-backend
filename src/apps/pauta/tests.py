import pytest
from mixer.backend.django import mixer
from apps.pauta.models import PautasGA
from django.db import IntegrityError


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
