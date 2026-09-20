from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .utils import get_or_create_user_folders

@receiver(post_save, sender=User)
def create_user_folders(sender, instance, created, **kwargs):
    if created:
        get_or_create_user_folders(instance)