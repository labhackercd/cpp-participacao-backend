from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.model_mixins import AnalysisMixin


class RoomAnalysisAudiencias(AnalysisMixin):
    room_id = models.IntegerField(verbose_name=_("id room"), db_index=True,
                                  null=True, blank=True, unique=True)
    meeting_code = models.IntegerField(verbose_name=_("id code in SILEG"),
                                       db_index=True, null=True, blank=True)


class GeneralAnalysisAudiencias(AnalysisMixin):
    pass

    class Meta:
        unique_together = ('start_date', 'period')


class AudienciasGA(AnalysisMixin):
    pass

    class Meta:
        unique_together = ('start_date', 'period')
