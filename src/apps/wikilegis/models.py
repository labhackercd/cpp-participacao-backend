from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.model_mixins import AnalysisMixin


class DocumentAnalysisWikilegis(AnalysisMixin):
    document_id = models.IntegerField(verbose_name=_("id room"), db_index=True,
                                      null=True, blank=True, unique=True)


class GeneralAnalysisWikilegis(AnalysisMixin):
    pass

    class Meta:
        unique_together = ('start_date', 'period')


class WikilegisGA(AnalysisMixin):
    pass

    class Meta:
        unique_together = ('start_date', 'period')
