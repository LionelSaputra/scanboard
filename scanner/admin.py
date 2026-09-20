from django.contrib import admin
from .models import Document, Folder
from django.utils.html import format_html

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'folder', 'uploaded_at', 'view_file')
    list_filter = ('user', 'folder', 'uploaded_at')

    def view_file(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Lihat File</a>', obj.file.url)
        return '-'
    view_file.short_description = 'File'


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'id')
    list_filter = ('user',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'folder', 'uploaded_at')
    list_filter = ('user', 'folder', 'uploaded_at')
