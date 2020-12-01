from django.contrib import admin

from .models import GeneralAnalysisAudiencias, RoomAnalysisAudiencias


@admin.register(GeneralAnalysisAudiencias)
class GeneralAnalysisAudienciasAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'start_date',
        'end_date',
        'period',
    )
    list_filter = ('created', 'modified', 'start_date', 'end_date', 'period')


@admin.register(RoomAnalysisAudiencias)
class RoomAnalysisAudienciasAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'start_date',
        'end_date',
        'period',
        'room_id',
        'meeting_code',
    )
    list_filter = ('created', 'modified', 'start_date', 'end_date')
