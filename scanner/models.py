from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings
import uuid
import os


def user_normal_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    username = slugify(instance.user.username)
    folder_name = slugify(instance.folder.name) if instance.folder else "default"

    return os.path.join(f'user_{instance.user.id}_{username}', folder_name, 'Normal', filename)



def user_ocr_text_path(instance, filename):
    filename = f"{uuid.uuid4().hex}.txt"
    username = slugify(instance.user.username)
    folder_name = slugify(instance.folder.name) if instance.folder else "default"

    return os.path.join(f'user_{instance.user.id}_{username}', folder_name, 'OCR', filename)



def user_smart_scan_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    username = slugify(instance.user.username)
    folder_name = slugify(instance.folder.name) if instance.folder else "default"

    return os.path.join(f'user_{instance.user.id}_{username}', folder_name, 'SmartScan', filename)



class Folder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'user')

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def save(self, *args, **kwargs):
        username = slugify(self.user.username)
        base_path = os.path.join(
            settings.MEDIA_ROOT,
            f'user_{self.user.id}_{username}',
            self.name  # <-- ini ganti 'ocr' jadi nama folder-nya
        )

        for subfolder in ['Normal', 'OCR', 'SmartScan']:
            os.makedirs(os.path.join(base_path, subfolder), exist_ok=True)

        super().save(*args, **kwargs)





class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to=user_normal_file_path, null=True, blank=True)
    text_file = models.FileField(upload_to=user_ocr_text_path, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ocr_text = models.TextField(null=True, blank=True)
    preview = models.ImageField(upload_to='previews/', null=True, blank=True)
    smart_scanned_file = models.ImageField(upload_to=user_smart_scan_path, null=True, blank=True)

    class Meta:
        unique_together = ('title', 'user')

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def delete(self, *args, **kwargs):
        # Hapus file secara fisik
        for field in [self.file, self.text_file, self.smart_scanned_file]:
            if field and os.path.isfile(field.path):
                os.remove(field.path)
        super().delete(*args, **kwargs)
