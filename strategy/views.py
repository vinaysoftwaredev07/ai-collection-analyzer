"""
Views for the strategy app.

Security:
  - All views require authentication (@login_required).
  - Data isolation enforced: agents see only their assigned borrowers.
  - File uploads validated by size, extension, and MIME type (magic bytes).
  - CSRF protection enabled on all endpoints (no @csrf_exempt).
  - Internal errors are logged and never exposed to the client.
"""
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import get_user_role
from .forms import BorrowerForm
from .llm_client import LLMWrapperClient
from .models import Borrower

logger = logging.getLogger(__name__)

# Allowed MIME types mapped from file extensions (magic-byte validation)
ALLOWED_MIME_TYPES = {
    'pdf': 'application/pdf',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}

# Magic byte signatures for basic MIME validation without python-magic
MAGIC_SIGNATURES = {
    b'%PDF': 'application/pdf',
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG': 'image/png',
}


def _validate_file_magic(file_bytes, expected_ext):
    """
    Validate file content against known magic byte signatures.
    Returns True if the file content matches the expected extension.
    """
    expected_mime = ALLOWED_MIME_TYPES.get(expected_ext)
    if not expected_mime:
        return False

    for signature, mime_type in MAGIC_SIGNATURES.items():
        if file_bytes[:len(signature)] == signature:
            return mime_type == expected_mime

    return False


def _get_borrower_queryset(user):
    """
    Return the appropriate borrower queryset based on user role.
    Supervisors see all borrowers; agents see only their assigned borrowers.
    """
    role = get_user_role(user)
    if role == 'supervisor':
        return Borrower.objects.all()
    return Borrower.objects.filter(assigned_agent=user)


def _can_access_borrower(user, borrower):
    """Check if a user has permission to access a specific borrower."""
    role = get_user_role(user)
    if role == 'supervisor':
        return True
    return borrower.assigned_agent == user


# ------------------------------------------------------------------
# Views
# ------------------------------------------------------------------

@login_required
def dashboard_view(request):
    """Dashboard showing borrowers filtered by user role."""
    role = get_user_role(request.user)
    if role == 'supervisor':
        borrowers = Borrower.objects.all()
    else:
        borrowers = Borrower.objects.filter(assigned_agent=request.user)
    return render(request, 'strategy/dashboard.html', {
        'borrowers': borrowers,
        'user_role': role,
    })


@login_required
def borrower_detail_view(request, pk):
    """Borrower detail page with AI strategy generation."""
    borrower = get_object_or_404(Borrower, pk=pk)

    # Enforce data isolation — single role lookup
    role = get_user_role(request.user)
    if role != 'supervisor' and borrower.assigned_agent != request.user:
        logger.warning(
            "Access denied: user=%s tried to access borrower pk=%s",
            request.user.username, pk,
        )
        return HttpResponseForbidden(
            "You do not have permission to view this borrower."
        )

    ai_strategy = None

    if request.method == 'POST':
        try:
            client = LLMWrapperClient()
            ai_strategy = client.generate_strategy(borrower)
            logger.info(
                "AI strategy generated for borrower pk=%s by user=%s",
                pk, request.user.username,
            )
        except Exception:
            logger.exception("Failed to generate AI strategy for borrower pk=%s", pk)
            ai_strategy = {
                "segment": "Error",
                "recommendedAction": "Manual Review",
                "messageDraft": "Unable to generate message. Please try again later.",
                "explanation": "An internal error occurred.",
            }

    return render(request, 'strategy/borrower_detail.html', {
        'borrower': borrower,
        'ai_strategy': ai_strategy,
    })


@login_required
def borrower_create_view(request):
    """Create a new borrower and auto-assign to the current user."""
    if request.method == 'POST':
        form = BorrowerForm(request.POST, request.FILES)
        if form.is_valid():
            borrower = form.save(commit=False)
            borrower.assigned_agent = request.user
            borrower.save()
            logger.info(
                "Borrower '%s' created by user=%s",
                borrower.name, request.user.username,
            )
            return redirect('dashboard')
    else:
        form = BorrowerForm()

    return render(request, 'strategy/borrower_form.html', {'form': form})


@login_required
def parse_document_view(request):
    """
    Parse an uploaded document (PDF/image) using the LLM wrapper API.
    Sends the file as base64 directly to the API for extraction.
    CSRF protection is active — the client must include the X-CSRFToken header.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    document = request.FILES.get('document')
    if not document:
        return JsonResponse({'error': 'No document provided.'}, status=400)

    # --- File size validation ---
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
    if document.size > max_size:
        max_mb = max_size / (1024 * 1024)
        return JsonResponse(
            {'error': f'File too large. Maximum size is {max_mb:.0f} MB.'},
            status=400,
        )

    # --- Extension validation ---
    ext = document.name.rsplit('.', 1)[-1].lower() if '.' in document.name else ''
    if ext not in ALLOWED_MIME_TYPES:
        return JsonResponse(
            {'error': f'Unsupported file type: .{ext}. Allowed: pdf, jpg, jpeg, png.'},
            status=400,
        )

    try:
        file_bytes = document.read()

        # --- Magic byte validation ---
        if not _validate_file_magic(file_bytes, ext):
            logger.warning(
                "File magic mismatch: user=%s uploaded '%s' with ext=%s",
                request.user.username, document.name, ext,
            )
            return JsonResponse(
                {'error': 'File content does not match its extension.'},
                status=400,
            )

        # --- PDF page count validation ---
        if ext == 'pdf':
            max_pages = getattr(settings, 'MAX_PDF_PAGES', 50)
            try:
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                page_count = doc.page_count
                doc.close()
                if page_count > max_pages:
                    return JsonResponse(
                        {'error': f'PDF has {page_count} pages. Maximum is {max_pages}.'},
                        status=400,
                    )
            except ImportError:
                logger.warning("PyMuPDF not installed; skipping PDF page count validation.")
            except Exception:
                logger.exception("Error reading PDF for page count validation.")

        # --- Send to LLM API as base64 ---
        client = LLMWrapperClient()
        parsed_data = client.parse_document_file(file_bytes, ext)

        if not parsed_data:
            return JsonResponse(
                {'error': 'Could not extract data from the document.'},
                status=400,
            )

        logger.info(
            "Document parsed successfully: user=%s file=%s",
            request.user.username, document.name,
        )
        return JsonResponse(parsed_data)

    except Exception:
        logger.exception(
            "Unexpected error parsing document: user=%s file=%s",
            request.user.username, document.name,
        )
        return JsonResponse(
            {'error': 'An internal error occurred while processing the document.'},
            status=500,
        )


@login_required
def serve_document(request, pk):
    """
    Serve an uploaded borrower document with access control.
    Only the assigned agent or a supervisor can download the file.
    This replaces direct /media/ URL access for borrower documents.
    """
    borrower = get_object_or_404(Borrower, pk=pk)

    # Enforce data isolation
    role = get_user_role(request.user)
    if role != 'supervisor' and borrower.assigned_agent != request.user:
        logger.warning(
            "Document access denied: user=%s tried to access document for borrower pk=%s",
            request.user.username, pk,
        )
        return HttpResponseForbidden(
            "You do not have permission to access this document."
        )

    if not borrower.document:
        return HttpResponseForbidden("No document attached to this borrower.")

    # Determine content type from extension
    filename = borrower.document.name.rsplit('/', 1)[-1]
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    content_type = ALLOWED_MIME_TYPES.get(ext, 'application/octet-stream')

    response = FileResponse(
        borrower.document.open('rb'),
        content_type=content_type,
    )
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

