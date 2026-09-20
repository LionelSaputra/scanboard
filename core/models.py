from django.contrib.auth.models import User
from django.db import models

class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    shared = models.BooleanField(default=False)
    share_link = models.CharField(max_length=100, blank=True, null=True)

class Document(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_filtered = models.BooleanField(default=False)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cloud_sync_enabled = models.BooleanField(default=False)
