from django.db import models
from django.utils.translation import gettext_lazy as _


class AnalysisMixin(models.Model):
    created = models.DateTimeField(_('created'), editable=False,
                                   blank=True, auto_now_add=True)
    modified = models.DateTimeField(_('modified'), editable=False,
                                    blank=True, auto_now=True)
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))
    data = models.JSONField(_('data'), null=True, blank=True)

    class Meta:
        abstract = True
