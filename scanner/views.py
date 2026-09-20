import os
import uuid
import requests
from PIL import Image, ImageEnhance, UnidentifiedImageError
import io
from django.core.files.base import ContentFile

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from .forms import DocumentForm, FolderForm
from .models import Document, Folder
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from PIL import Image, ImageEnhance, ImageFilter
from django.views.decorators.http import require_POST
import cv2
import numpy as np

# def hybrid_preprocess(image_path):
#     try:
#         # OpenCV grayscale + resize + denoise
#         img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
#         img = cv2.resize(img, (0, 0), fx=2, fy=2)
#         img = cv2.GaussianBlur(img, (5, 5), 0)
#         _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#         img = cv2.fastNlMeansDenoising(img, None, 30, 7, 21)

#         # Convert ke PIL untuk tingkatkan kontras
#         pil_img = Image.fromarray(img)
#         enhancer = ImageEnhance.Contrast(pil_img)
#         pil_img = enhancer.enhance(2.0)

#         output = io.BytesIO()
#         pil_img.save(output, format='PNG')
#         output.seek(0)
#         return output
#     except Exception as e:
#         print("❌ Hybrid Preprocessing error:", e)
#         return None

@csrf_exempt
@login_required
def smart_scan_preview(request, pk):
    document = get_object_or_404(Document, id=pk)
    image_path = document.image.path
    img = cv2.imread(image_path)

    if img is None:
        return HttpResponse("Image not found", status=404)

    # Basic filter: grayscale + threshold
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    filtered = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 10
    )

    # Encode as PNG and return
    is_success, buffer = cv2.imencode(".png", filtered)
    if not is_success:
        return HttpResponse("Error encoding image", status=500)

    return HttpResponse(buffer.tobytes(), content_type="image/png")


def smart_scan(request, pk):
    document = get_object_or_404(Document, pk=pk)

    if document.file:
        processed_bytes = smart_scan_in_memory(document.file.path)
        if processed_bytes:
            filename = f"{uuid.uuid4().hex}_smartscan.png"
            document.smart_scanned_file.save(filename, ContentFile(processed_bytes.getvalue()))
            document.save()
            messages.success(request, "Smart Scan berhasil.")
        else:
            messages.error(request, "Gagal melakukan Smart Scan.")
    return redirect('document_list')

@require_POST
@login_required
def detect_text(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)

    if document.file and is_image(document.file.path):
        processed_path = preprocess_image(document.file.path)
        # processed_io = hybrid_preprocess(document.file.path)
        ocr_text = extract_text_with_ocr_space(processed_path)

        if ocr_text:
            document.ocr_text = ocr_text

            # ✅ Simpan hasil OCR ke field text_file
            txt_filename = f"{uuid.uuid4().hex}.txt"
            document.text_file.save(txt_filename, ContentFile(ocr_text), save=False)
            document.save()

    return redirect('document_list')



@login_required(login_url='/core/login/')
def document_list(request):
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    folders = Folder.objects.filter(user=request.user)

    for doc in documents:
        doc.has_text = bool(doc.ocr_text)
        doc.has_smart_scan = bool(doc.smart_scanned_file)

    return render(request, 'scanner/document_list.html', {
        'documents': documents,
        'folders': folders
    })



@login_required(login_url='/core/login/')
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES.get('file')
            title = form.cleaned_data.get('title')
            folder = form.cleaned_data.get('folder')

            username = request.user.username  # ✅ Didefinisikan lebih awal
            folder_name = folder.name if folder else 'default'

            if Document.objects.filter(title=title, user=request.user).exists():
                messages.error(request, f"Dokumen dengan nama '{title}' sudah ada.")
                return redirect('upload_document')

            if Folder.objects.filter(name=title, user=request.user).exists():
                messages.error(request, f"Nama '{title}' sudah digunakan sebagai folder.")
                return redirect('upload_document')

            document = form.save(commit=False)
            document.user = request.user
            document.folder = folder
            document.save()

            # Smart Scan
            if form.cleaned_data.get('smart_scan') and is_image(document.file.path):
                processed_bytes = smart_scan_in_memory(document.file.path)
                if processed_bytes:
                    preview_filename = f"{uuid.uuid4().hex}_preview.png"
                    # scan_filename = f"{uuid.uuid4().hex}_smartscan.png"

                    # # Simpan preview (untuk thumbnail)
                    # # document.preview.save(preview_filename, ContentFile(processed_bytes.getvalue()), save=False)

                    # # Simpan file hasil smart scan permanen
                    # document.smart_scanned_file.save(scan_filename, ContentFile(processed_bytes.getvalue()), save=False)
                    scan_filename = f"{uuid.uuid4().hex}_smartscan.png"
                    document.smart_scanned_file.save(scan_filename, ContentFile(processed_bytes.getvalue()), save=False)
                    document.save()

            # Image to Text (OCR)
            if form.cleaned_data.get('detect_text') and is_image(document.file.path):
                processed_path = preprocess_image(document.file.path)
                # processed_io = hybrid_preprocess(document.file.path)
                ocr_text = extract_text_with_ocr_space(processed_path)

                if ocr_text:
                    document.ocr_text = ocr_text
                    document.save()

                    # Simpan hasil OCR sebagai file txt
                    if ocr_text:
                        # username = request.user.username
                        # folder_name = folder.name if folder else 'default'
                        # ocr_folder_path = f"user_{request.user.id}_{username}/ocr/{folder_name}/OCR/"
                        # txt_filename = f"{uuid.uuid4().hex}.txt"
                        # document.text_file.save(os.path.join(ocr_folder_path, txt_filename), ContentFile(ocr_text), save=False)
                        # txt_filename = f"{uuid.uuid4().hex}.txt"
                        # document.text_file.save(txt_filename, ContentFile(ocr_text), save=False)
                        txt_filename = f"{uuid.uuid4().hex}.txt"
                        document.text_file.save(txt_filename, ContentFile(ocr_text), save=False)
                        document.save()

                    # except Exception as e:
                    #     print(f"⚠️ Gagal menyimpan file .txt: {e}")

            messages.success(request, "Dokumen berhasil diunggah.")
            return redirect('document_list')
    else:
        form = DocumentForm()
        form.fields['folder'].queryset = Folder.objects.filter(user=request.user)

    # document.save()

    return render(request, 'scanner/upload.html', {'form': form})


@login_required(login_url='/core/login/')
def create_folder(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')

            if Folder.objects.filter(name=name, user=request.user).exists():
                messages.error(request, f"Folder dengan nama '{name}' sudah ada.")
                return redirect('create_folder')

            if Document.objects.filter(title=name, user=request.user).exists():
                messages.error(request, f"Nama '{name}' sudah digunakan sebagai dokumen.")
                return redirect('create_folder')

            folder = form.save(commit=False)
            folder.user = request.user
            folder.save()

            messages.success(request, f"Folder '{name}' berhasil dibuat.")
            return redirect('document_list')
    else:
        form = FolderForm()

    return render(request, 'scanner/create_folder.html', {'form': form})


@login_required(login_url='/core/login/')
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)

    # Simpan path-path file
    original_file_path = document.file.path if document.file else None
    smart_scan_path = document.smart_scanned_file.path if document.smart_scanned_file else None

    # Hapus file utama
    if document.file and document.file.name and document.file.storage.exists(document.file.name):
        try:
            document.file.delete(save=False)
        except Exception as e:
            print(f"⚠️ Gagal menghapus file utama: {e}")

    # Hapus file hasil Smart Scan
    if smart_scan_path and os.path.exists(smart_scan_path):
        try:
            os.remove(smart_scan_path)
            print(f"🗑️ File Smart Scan terhapus: {smart_scan_path}")
        except Exception as e:
            print(f"⚠️ Gagal menghapus file Smart Scan: {e}")

    # Hapus file .txt dan _processed.png (jika ada)
    if original_file_path:
        related_files = [
            os.path.splitext(original_file_path)[0] + ".txt",             # file txt hasil OCR
            os.path.splitext(original_file_path)[0] + "_processed.png",   # gambar hasil preprocessing
        ]

        for path in related_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"🗑️ File terhapus: {path}")
                except Exception as e:
                    print(f"⚠️ Gagal menghapus {path}: {e}")

    # Hapus instance di database
    document.delete()
    messages.success(request, "Dokumen & semua file terkait berhasil dihapus.")
    return redirect('document_list')


@login_required(login_url='/core/login/')
def view_text(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    text = document.ocr_text or "[Teks belum tersedia.]"
    return render(request, 'scanner/view_text.html', {
        'document': document,
        'text': text
    })


@login_required(login_url='/core/login/')
def view_image(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    return render(request, 'scanner/view_image.html', {'document': document})


@login_required(login_url='/core/login/')
def upload_success(request):
    return render(request, 'scanner/success.html')


def is_image(image_path):
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, IOError):
        return False


# def preprocess_image(image_path):
#     try:
#         img = Image.open(image_path)
#         img = img.convert('L')  # Grayscale
#         img.thumbnail((1024, 1024))  # Resize to max 1024x1024
#         enhancer = ImageEnhance.Contrast(img)
#         img = enhancer.enhance(2.0)

#         output = io.BytesIO()
#         img.save(output, format='PNG', optimize=True)  # Optimize to reduce size
#         output.seek(0)
#         return output
#     except Exception as e:
#         print("❌ Error saat preprocessing:", e)
#         return None

def preprocess_image(image_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (0, 0), fx=2, fy=2)  # Upscale
        img = cv2.GaussianBlur(img, (5, 5), 0)
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        img = cv2.fastNlMeansDenoising(img, None, 30, 7, 21)

        is_success, buffer = cv2.imencode(".png", img)
        if is_success:
            return io.BytesIO(buffer.tobytes())
    except Exception as e:
        print("❌ Error saat preprocessing:", e)
    return None



def smart_scan_in_memory(image_path):
    try:
        img = Image.open(image_path)
        img = img.convert('L')
        img = img.resize((img.width * 2, img.height * 2))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)

        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        return output
    except Exception as e:
        print("❌ Smart Scan error:", e)
        return None
    
    #     try:
    #     img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    #     img = cv2.resize(img, (0, 0), fx=2, fy=2)  # Upscale
    #     img = cv2.GaussianBlur(img, (5, 5), 0)
    #     _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #     img = cv2.fastNlMeansDenoising(img, None, 30, 7, 21)

    #     is_success, buffer = cv2.imencode(".png", img)
    #     if is_success:
    #         return io.BytesIO(buffer.tobytes())
    # except Exception as e:
    #     print("❌ Error saat preprocessing:", e)
    # return None

def extract_text_with_ocr_space(image_io, lang='ind'):
    api_key = getattr(settings, 'OCR_SPACE_API_KEY', None)
    if not api_key:
        print("⚠️ API Key tidak ditemukan.")
        return ""

    try:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'filename': ('image.png', image_io)},
            data={
                'apikey': api_key,
                'language': 'eng',
                'scale': True,
                # 'isOverlayRequired': False,
                # 'detectOrientation': True,
                'OCREngine': 1,
            },
            timeout=getattr(settings, 'OCR_REQUEST_TIMEOUT', 30)
        )
        result = response.json()

        if result.get("IsErroredOnProcessing"):
            print("❌ OCR Error:", result.get("ErrorMessage"))
            return ""

        return result['ParsedResults'][0]['ParsedText']
    except requests.exceptions.Timeout:
        print("❌ OCR Error: Timeout saat menghubungi API OCR.Space.")
        return ""
    except Exception as e:
        print("❌ Error saat memproses OCR:", e)
        return ""


@login_required(login_url='/core/login/')
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    return render(request, 'scanner/document_detail.html', {'document': document})
