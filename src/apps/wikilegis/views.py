from rest_framework import viewsets
from rest_framework import mixins
from apps.wikilegis.models import DocumentAnalysisWikilegis
from apps.wikilegis.serializers import DocumentAnalysisWikilegisSerializer


class ListViewSetDocumentAnalysisWikilegis(mixins.ListModelMixin,
                                           viewsets.GenericViewSet):
    serializer_class = DocumentAnalysisWikilegisSerializer

    def get_queryset(self):
        documents = DocumentAnalysisWikilegis.objects.all()

        return documents
