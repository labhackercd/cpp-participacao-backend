from rest_framework import viewsets
from rest_framework import mixins
from apps.audiencias.models import GeneralAnalysisAudiencias
from apps.audiencias.serializers import GeneralAnalysisAudienciasSerializer


class ListViewSetGeneralAnalysisAudiencias(mixins.ListModelMixin,
                                           viewsets.GenericViewSet):
    serializer_class = GeneralAnalysisAudienciasSerializer

    def get_queryset(self):
        analysis = GeneralAnalysisAudiencias.objects.all()

        return analysis