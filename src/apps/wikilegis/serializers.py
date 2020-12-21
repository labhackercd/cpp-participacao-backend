from rest_framework import serializers
from apps.wikilegis.models import DocumentAnalysisWikilegis


class DocumentAnalysisWikilegisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysisWikilegis
        fields = '__all__'
