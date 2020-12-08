from django.contrib import admin

from .models import PautasGA
from django.db import models
from django_json_widget.widgets import JSONEditorWidget


@admin.register(PautasGA)
class PautasGAAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    list_display = ('id', 'start_date', 'end_date', 'period', 'data')
    list_filter = ('start_date', 'end_date', 'modified', 'period')
