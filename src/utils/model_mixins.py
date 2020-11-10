from django.db import models
import json


class AnalysisMixin(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    _data = models.TextField(null=True, blank=True)

    @property
    def data(self):
        if self._data:
            return json.loads(self._data)
        else:
            return {}

    @data.setter
    def data(self, value):
        self._data = json.dumps(value)

    class Meta:
        abstract = True