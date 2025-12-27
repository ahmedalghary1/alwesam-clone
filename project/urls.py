from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns


urlpatterns = [
    # تغيير اللغة (set_language)
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),

    path('accounts/', include('allauth.urls')),
    path('account/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('', include('home.urls')),
    path('products/', include('products.urls')),
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),
    path('admin-panel/', include('admin_panel.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
