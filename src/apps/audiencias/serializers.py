from rest_framework import serializers
from apps.audiencias.models import GeneralAnalysisAudiencias


class GeneralAnalysisAudienciasSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralAnalysisAudiencias
        fields = '__all__'
