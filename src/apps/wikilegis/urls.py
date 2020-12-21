from rest_framework import routers
from apps.wikilegis.views import ListViewSetDocumentAnalysisWikilegis

router = routers.SimpleRouter()
router.register(r'wikilegis-documents',
                ListViewSetDocumentAnalysisWikilegis,
                basename='wikilegis-documents')

urlpatterns = router.urls
