import os
from django.conf import settings

def get_or_create_user_folders(user):
    base_path = os.path.join(settings.MEDIA_ROOT, 'documents', f'user_{user.id}')
    normal_path = os.path.join(base_path, 'Normal')
    smartscan_path = os.path.join(base_path, 'SmartScan')

    os.makedirs(normal_path, exist_ok=True)
    os.makedirs(smartscan_path, exist_ok=True)
