from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.model_mixins import AnalysisMixin


class GeneralAnalysisAudiencias(AnalysisMixin):
    pass


class RoomAnalysisAudiencias(AnalysisMixin):
    room_id = models.IntegerField(verbose_name=_("id room"), db_index=True)
    title = models.CharField(verbose_name=_("title"), max_length=200)
    meeting_code = models.IntegerField(verbose_name=_("id code in SILEG"),
                                       db_index=True)
