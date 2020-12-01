from django.db import models
from django.utils.translation import gettext_lazy as _


class AnalysisMixin(models.Model):
    PERIOD_CHOICES = (
        ('daily', _('Daily')),
        ('monthly', _('Monthly')),
        ('semiannually', _('Semiannually')),
        ('yearly', _('Yearly')),
        ('all', _('All the time')),
    )
    created = models.DateTimeField(_('created'), editable=False,
                                   blank=True, auto_now_add=True)
    modified = models.DateTimeField(_('modified'), editable=False,
                                    blank=True, auto_now=True)
    start_date = models.DateField(_('start date'), db_index=True)
    end_date = models.DateField(_('end date'), db_index=True)
    data = models.JSONField(_('data'), null=True, blank=True)
    period = models.CharField(_('period'), max_length=200, db_index=True,
                              choices=PERIOD_CHOICES, default='daily')

    class Meta:
        abstract = True
