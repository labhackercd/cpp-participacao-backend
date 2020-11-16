from django.contrib import admin

from .models import GeneralAnalysisAudiencias, RoomAnalysisAudiencias


@admin.register(GeneralAnalysisAudiencias)
class GeneralAnalysisAudienciasAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'data')
    list_filter = ('start_date', 'end_date')


@admin.register(RoomAnalysisAudiencias)
class RoomAnalysisAudienciasAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'start_date',
        'end_date',
        'data',
        'room_id',
        'meeting_code',
    )
    list_filter = ('start_date', 'end_date')
