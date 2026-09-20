from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('upload/', views.upload_document, name='upload_document'),
    path('upload/success/', views.upload_success, name='upload_success'),
    path('delete/<uuid:document_id>/', views.delete_document, name='delete_document'),
    path('view_text/<uuid:document_id>/', views.view_text, name='view_text'),
    path('view_image/<uuid:document_id>/', views.view_image, name='view_image'),
    path('create_folder/', views.create_folder, name='create_folder'),
    path('document/<uuid:pk>/', views.document_detail, name='document_detail'),
    path('smart-scan/<uuid:pk>/', views.smart_scan, name='smart_scan'),
    path('smart-scan-preview/<uuid:pk>/', views.smart_scan_preview, name='smart_scan_preview'),
    path('detect-text/<uuid:pk>/', views.detect_text, name='detect_text'),  # ✅ Tambahan ini
    path('logout/', LogoutView.as_view(next_page='/core/login/'), name='logout'),
]
