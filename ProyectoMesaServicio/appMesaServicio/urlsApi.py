from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('oficinaambiente/',views.OficinaAmbienteList.as_view()),
    path('oficinaambiente/<int:pk>/',views.OficinaAmbienteDetail.as_view()),
    path('docs/',include_docs_urls(title='Documentation API'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
