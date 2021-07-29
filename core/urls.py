# -*- encoding: utf-8 -*-
import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path

from app.views import pages, CurrencyToEpicJsonView

urlpatterns = [
    re_path(r'^.*\.*html', pages, name='pages'),
    # path("main/", include("app.urls")),
    path('admin/', admin.site.urls),
    # path('blog', include("blog.urls")),
    path("", include("app.urls")),
    # path("wallet/", include("wallet.urls")),
    # path("swapic/", include("swapic.urls")),
    # path("app/", include("ecb.urls")),
    path("epic_to_currency/", CurrencyToEpicJsonView.as_view(), name='epic_to_currency'),
    path('mining/', include("mining.urls")),
    # path("", include("authentication.urls")),
    path('api-auth/', include('rest_framework.urls')),
    # path('qr_code/', include('qr_code.urls', namespace="qr_code")),
    path('__debug__/', include(debug_toolbar.urls)),

    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
