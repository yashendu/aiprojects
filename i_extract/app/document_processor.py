import os
import re
import io
import base64
import json
from PIL import Image

SUPPORTED_DOCS = {'.pdf'}
SUPPORTED_IMAGES = {'.jpg', '.jpeg'}

MAX_PDF_PAGES = 50
PDF_RENDER_DPI = 150

try:
    from docling.document_converter import DocumentConverter
    HAS_DOCLING = True
except (ImportError, RecursionError):
    HAS_DOCLING = False

try:
    from app.surya_ocr import ocr_image as _surya_ocr_image, ocr_images as _surya_ocr_images, HAS_SURYA
except ImportError:
    HAS_SURYA = False


def _page_to_pil(page):
    img_data = page.get('image_data', '')
    if img_data and img_data.startswith('data:image/'):
        b64 = img_data.split(',', 1)[1]
        try:
            img_bytes = base64.b64decode(b64)
            return Image.open(io.BytesIO(img_bytes))
        except Exception:
            return None
    img_path = page.get('image_path')
    if img_path and os.path.exists(img_path):
        try:
            return Image.open(img_path)
        except Exception:
            return None
    return None


def _maybe_ocr_with_surya(pages, langs=None):
    if not HAS_SURYA:
        return
    images = []
    valid_indices = []
    for i, page in enumerate(pages):
        img = _page_to_pil(page)
        if img is not None:
            images.append(img)
            valid_indices.append(i)
    if not images:
        return
    try:
        texts = _surya_ocr_images(images, langs=langs)
        for idx, text in zip(valid_indices, texts):
            if text and text.strip():
                pages[idx]['text'] = text
    except Exception:
        pass


def load_pdf(filepath):
    if HAS_DOCLING:
        try:
            pages = _load_pdf_docling(filepath)
            _maybe_ocr_with_surya(pages)
            return pages
        except Exception:
            pass
    pages = _load_pdf_pymupdf(filepath)
    _maybe_ocr_with_surya(pages)
    return pages


def load_image(filepath):
    if HAS_DOCLING:
        try:
            return _load_image_docling(filepath)
        except Exception:
            pass
    img = Image.open(filepath)
    text = ''
    if HAS_SURYA:
        try:
            ocr_text = _surya_ocr_image(filepath)
            if ocr_text and ocr_text.strip():
                text = ocr_text
        except Exception:
            pass
    return [{'page': 1, 'text': text, 'width': img.width, 'height': img.height, 'image_path': filepath}]


def _load_pdf_docling(filepath):
    import fitz
    pdf_doc = fitz.open(filepath)
    zoom = PDF_RENDER_DPI / 72
    mat = fitz.Matrix(zoom, zoom)

    converter = DocumentConverter()
    result = converter.convert(filepath)
    dl_doc = result.document

    pages = []
    for i, page in enumerate(pdf_doc):
        if i >= MAX_PDF_PAGES:
            break

        dl_page = dl_doc.pages.get(i + 1)
        text = dl_page.text if dl_page and dl_page.text else ''

        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes('jpeg')
        b64_img = base64.b64encode(img_bytes).decode()

        line_data = []
        if dl_page:
            for item in dl_page.items:
                txt = getattr(item, 'text', '') or ''
                if txt.strip():
                    bbox = item.bbox
                    line_data.append({
                        'text': txt.strip(),
                        'bbox_px': [
                            round(v * zoom, 1)
                            for v in (bbox.l, bbox.t, bbox.r, bbox.b)
                        ],
                    })

        if not line_data:
            blocks = page.get_text('dict')['blocks']
            for block in blocks:
                if block.get('type') == 0:
                    for line in block['lines']:
                        bbox = line['bbox']
                        line_text = ''.join(span['text'] for span in line['spans'])
                        if line_text.strip():
                            line_data.append({
                                'text': line_text.strip(),
                                'bbox_px': [round(v * zoom, 1) for v in bbox],
                            })

        pages.append({
            'page': i + 1,
            'text': text,
            'image_data': f'data:image/jpeg;base64,{b64_img}',
            'img_w': pix.width,
            'img_h': pix.height,
            'width': page.rect.width,
            'height': page.rect.height,
            'lines': line_data,
        })

    pdf_doc.close()
    return pages


def _load_image_docling(filepath):
    converter = DocumentConverter()
    result = converter.convert(filepath)
    dl_doc = result.document

    text = dl_doc.export_to_text() if hasattr(dl_doc, 'export_to_text') else (dl_doc.text or '')
    from PIL import Image
    img = Image.open(filepath)
    return [{'page': 1, 'text': text, 'width': img.width, 'height': img.height, 'image_path': filepath}]


def _load_pdf_pymupdf(filepath):
    import fitz
    doc = fitz.open(filepath)
    pages = []
    zoom = PDF_RENDER_DPI / 72
    mat = fitz.Matrix(zoom, zoom)
    for i, page in enumerate(doc):
        if i >= MAX_PDF_PAGES:
            break
        text = page.get_text()
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes('jpeg')
        b64_img = base64.b64encode(img_bytes).decode()
        image_data = f'data:image/jpeg;base64,{b64_img}'

        line_data = []
        blocks = page.get_text('dict')['blocks']
        for block in blocks:
            if block.get('type') == 0:
                for line in block['lines']:
                    bbox = line['bbox']
                    line_text = ''.join(span['text'] for span in line['spans'])
                    if line_text.strip():
                        line_data.append({
                            'text': line_text.strip(),
                            'bbox_px': [round(v * zoom, 1) for v in bbox],
                        })

        pages.append({
            'page': i + 1,
            'text': text,
            'image_data': image_data,
            'img_w': pix.width,
            'img_h': pix.height,
            'width': page.rect.width,
            'height': page.rect.height,
            'lines': line_data,
        })
    doc.close()
    return pages


def normalize_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_text(pages):
    return '\n\n'.join(p['text'] for p in pages if p['text'].strip())


def render_document_html(pages):
    parts = []
    for p in pages:
        text = p.get('text', '')
        if p.get('image_data'):
            spans = _text_to_spans(text)
            lines_json = json.dumps(p.get('lines', []))
            parts.append(
                f'<div class="doc-page" data-page="{p["page"]}" data-img-w="{p["img_w"]}" data-img-h="{p["img_h"]}" data-lines=\'{lines_json}\'>'
                f'<div class="doc-img-wrap">'
                f'<img src="{p["image_data"]}" style="width:100%;display:block;" class="doc-img">'
                f'<div class="hl-overlay" id="hl-overlay-{p["page"]}"></div>'
                f'</div>'
                f'</div>'
            )
        elif p.get('image_path'):
            img_data = _image_to_b64(p['image_path'])
            parts.append(f'<div class="doc-page" data-page="{p["page"]}"><div class="doc-img-wrap"><img src="{img_data}" style="width:100%" class="doc-img"></div></div>')
        elif text.strip():
            safe = _escape_html(text)
            lines = safe.split('\n')
            wrapped = ''.join(
                f'<span class="doc-line" data-line="{i + 1}">{line}</span>\n'
                for i, line in enumerate(lines) if line.strip()
            )
            parts.append(f'<div class="doc-page" data-page="{p["page"]}"><pre class="doc-text">{wrapped}</pre></div>')
        else:
            parts.append(f'<div class="doc-page" data-page="{p["page"]}"><p class="doc-empty">[No readable text on this page]</p></div>')
    return '\n'.join(parts)


def _text_to_spans(text):
    if not text.strip():
        return ''
    safe = _escape_html(text)
    lines = safe.split('\n')
    return ''.join(
        f'<span class="doc-line" data-line="{i + 1}">{line}</span>\n'
        for i, line in enumerate(lines) if line.strip()
    )


def _image_to_b64(filepath):
    with open(filepath, 'rb') as f:
        return f'data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}'


def _escape_html(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))


def supported_extensions():
    return sorted(SUPPORTED_DOCS | SUPPORTED_IMAGES)
