from django.contrib import admin

from .models import EdemocraciaGA, EdemocraciaAnalysis


@admin.register(EdemocraciaGA)
class EdemocraciaGAAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'period', 'data')
    list_filter = ('start_date', 'end_date', 'modified', 'period')


@admin.register(EdemocraciaAnalysis)
class EdemocraciaAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'period', 'data')
    list_filter = ('start_date', 'end_date', 'modified', 'period')
