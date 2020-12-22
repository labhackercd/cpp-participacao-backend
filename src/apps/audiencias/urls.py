from rest_framework import routers
from apps.audiencias.views import ListViewSetGeneralAnalysisAudiencias

router = routers.SimpleRouter()
router.register(r'audiencias-general',
                ListViewSetGeneralAnalysisAudiencias,
                basename='audiencias-general')

urlpatterns = router.urls
