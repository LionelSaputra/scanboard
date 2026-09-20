from django import forms
from .models import Document, Folder

class DocumentForm(forms.ModelForm):
    # Tambahkan dua opsi terpisah untuk OCR dan Smart Scan
    detect_text = forms.BooleanField(required=False, label='Image to Text (OCR)')
    smart_scan = forms.BooleanField(required=False, label='Smart Scan (Enhance & Preview)')

    class Meta:
        model = Document
        fields = ['title', 'file', 'folder', 'detect_text', 'smart_scan']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['folder'].queryset = Folder.objects.filter(user=user)

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']
