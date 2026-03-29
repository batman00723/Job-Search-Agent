from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from myapi.api import api_v1

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api_v1/', api_v1.urls)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

