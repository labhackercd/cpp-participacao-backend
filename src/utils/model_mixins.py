from django.db import models
import json


class AnalysisMixin(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    data = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True