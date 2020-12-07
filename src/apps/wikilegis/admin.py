from django.contrib import admin

from .models import (DocumentAnalysisWikilegis,
                     GeneralAnalysisWikilegis, WikilegisGA)
from django.db import models
from django_json_widget.widgets import JSONEditorWidget


@admin.register(DocumentAnalysisWikilegis)
class DocumentAnalysisWikilegisAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    list_display = (
        'id',
        'created',
        'modified',
        'start_date',
        'end_date',
        'period',
        'document_id',
    )
    list_filter = ('created', 'modified', 'start_date', 'end_date', 'period')


@admin.register(GeneralAnalysisWikilegis)
class GeneralAnalysisWikilegisAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    list_display = (
        'id',
        'created',
        'modified',
        'start_date',
        'end_date',
        'period',
    )
    list_filter = ('created', 'modified', 'start_date', 'end_date', 'period')


@admin.register(WikilegisGA)
class WikilegisGAAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    list_display = (
        'id',
        'created',
        'modified',
        'start_date',
        'end_date',
        'period',
    )
    list_filter = ('created', 'modified', 'start_date', 'end_date', 'period')
