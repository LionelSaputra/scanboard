from django.contrib import admin
from django.urls import path, include  # <-- sudah ditambah include
from core import views as core_views
from scanner import views as scanner_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/login/')),  # Redirect ke login page
    path('admin/', admin.site.urls),
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),
    path('register/', core_views.register_view, name='register'),
    # path('upload/', scanner_views.upload_document, name='upload_document'),
    # path('upload/success/', scanner_views.upload_success, name='upload_success'),
    # path('documents/', scanner_views.document_list, name='document_list'),
    path('scanner/', include('scanner.urls')),  # <-- ganti dari '' jadi scanner/
    path('core/', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
