from django.contrib import admin

from .models import (GeneralAnalysisAudiencias,
                     RoomAnalysisAudiencias, AudienciasGA)
from django.db import models
from django_json_widget.widgets import JSONEditorWidget


@admin.register(GeneralAnalysisAudiencias)
class GeneralAnalysisAudienciasAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    list_display = (
        'id',
        'start_date',
        'end_date',
        'period',
    )
    list_filter = ('created', 'modified', 'start_date', 'end_date', 'period')


@admin.register(RoomAnalysisAudiencias)
class RoomAnalysisAudienciasAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    list_display = (
        'id',
        'start_date',
        'end_date',
        'period',
        'room_id',
        'meeting_code',
    )
    list_filter = ('created', 'modified', 'start_date', 'end_date')


@admin.register(AudienciasGA)
class AudienciasGAAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    list_display = (
        'id',
        'start_date',
        'end_date',
        'period',
    )
    list_filter = ('created', 'modified', 'start_date', 'end_date', 'period')
