from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static


if settings.URL_PREFIX:
    prefix = '%s/' % (settings.URL_PREFIX)
else:
    prefix = ''

schema_view = get_schema_view(
    openapi.Info(
        title="Linguagem Simples API",
        default_version='v1',
        description="Este projeto tem como finalidade servir dados para um \
                    dashboard que possibilitará aos servidores da CPP \
                    acompanhar como está a participação dos usuários nas \
                    ferramentas da Câmara",
        contact=openapi.Contact(email="labhacker@camara.leg.br"),
        license=openapi.License(name="GNU General Public License v3.0"),
    ),
    url=prefix + "api/",
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

urlpatterns = [path(prefix, include(urlpatterns))]

admin.site.site_header = 'CPP Participação Backend'
