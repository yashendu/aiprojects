import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image


class TestPageToPil:
    def test_with_image_data(self):
        from app.document_processor import _page_to_pil
        img = Image.new('RGB', (100, 50), color='red')
        import io, base64
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        b64 = base64.b64encode(buf.getvalue()).decode()
        page = {'image_data': f'data:image/jpeg;base64,{b64}'}
        result = _page_to_pil(page)
        assert result is not None
        assert result.width == 100
        assert result.height == 50

    def test_with_image_path(self):
        from app.document_processor import _page_to_pil
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (200, 100), color='blue')
            img.save(f, format='JPEG')
            fname = f.name
        try:
            page = {'image_path': fname}
            result = _page_to_pil(page)
            assert result is not None
            assert result.width == 200
            assert result.height == 100
        finally:
            os.unlink(fname)

    def test_no_image_source(self):
        from app.document_processor import _page_to_pil
        assert _page_to_pil({'text': 'hello'}) is None

    def test_empty_page(self):
        from app.document_processor import _page_to_pil
        assert _page_to_pil({}) is None

    def test_invalid_base64(self):
        from app.document_processor import _page_to_pil
        page = {'image_data': 'data:image/jpeg;base64,invalid!!!'}
        assert _page_to_pil(page) is None


class TestMaybeOcrWithSurya:
    @patch('app.document_processor.HAS_SURYA', False)
    def test_noop_when_surya_unavailable(self):
        from app.document_processor import _maybe_ocr_with_surya
        pages = [{'text': ''}]
        _maybe_ocr_with_surya(pages)
        assert pages[0]['text'] == ''

    @patch('app.document_processor.HAS_SURYA', True)
    @patch('app.document_processor._surya_ocr_images')
    @patch('app.document_processor._page_to_pil')
    def test_calls_surya_on_all_pages(self, mock_page_to_pil, mock_ocr_images):
        from app.document_processor import _maybe_ocr_with_surya
        mock_page_to_pil.side_effect = [MagicMock(), MagicMock()]
        mock_ocr_images.return_value = ['Surya page 1', 'Surya page 2']
        pages = [
            {'text': '', 'image_data': 'data:image/jpeg;base64,dGVzdDE='},
            {'text': '', 'image_data': 'data:image/jpeg;base64,dGVzdDI='},
        ]
        _maybe_ocr_with_surya(pages)
        assert pages[0]['text'] == 'Surya page 1'
        assert pages[1]['text'] == 'Surya page 2'
        assert mock_ocr_images.call_count == 1
        assert len(mock_ocr_images.call_args[0][0]) == 2

    @patch('app.document_processor.HAS_SURYA', True)
    @patch('app.document_processor._surya_ocr_images')
    @patch('app.document_processor._page_to_pil')
    def test_skips_pages_without_images(self, mock_page_to_pil, mock_ocr_images):
        from app.document_processor import _maybe_ocr_with_surya
        mock_page_to_pil.return_value = None
        mock_ocr_images.return_value = ['should not be used']
        pages = [{'text': ''}]
        _maybe_ocr_with_surya(pages)
        mock_ocr_images.assert_not_called()

    @patch('app.document_processor.HAS_SURYA', True)
    @patch('app.document_processor._surya_ocr_images')
    @patch('app.document_processor._page_to_pil')
    def test_handles_ocr_exception(self, mock_page_to_pil, mock_ocr_images):
        from app.document_processor import _maybe_ocr_with_surya
        mock_page_to_pil.return_value = MagicMock()
        mock_ocr_images.side_effect = RuntimeError("OCR failed")
        pages = [{'text': '', 'image_data': 'data:image/jpeg;base64,dGVzdA=='}]
        _maybe_ocr_with_surya(pages)
        assert pages[0]['text'] == ''


class TestLoadPdf:
    @patch('app.document_processor.HAS_DOCLING', False)
    @patch('app.document_processor._load_pdf_pymupdf')
    @patch('app.document_processor._maybe_ocr_with_surya')
    def test_pymupdf_path(self, mock_surya, mock_pymupdf):
        from app.document_processor import load_pdf
        mock_pymupdf.return_value = [{'page': 1, 'text': 'hello'}]
        result = load_pdf('/fake/path.pdf')
        assert result[0]['text'] == 'hello'
        mock_surya.assert_called_once()

    @patch('app.document_processor.HAS_DOCLING', True)
    @patch('app.document_processor._load_pdf_docling')
    @patch('app.document_processor._load_pdf_pymupdf')
    @patch('app.document_processor._maybe_ocr_with_surya')
    def test_docling_path(self, mock_surya, mock_pymupdf, mock_docling):
        from app.document_processor import load_pdf
        mock_docling.return_value = [{'page': 1, 'text': 'docling text'}]
        result = load_pdf('/fake/path.pdf')
        assert result[0]['text'] == 'docling text'
        mock_pymupdf.assert_not_called()
        mock_surya.assert_called_once()

    @patch('app.document_processor.HAS_DOCLING', True)
    @patch('app.document_processor._load_pdf_docling')
    @patch('app.document_processor._load_pdf_pymupdf')
    @patch('app.document_processor._maybe_ocr_with_surya')
    def test_docling_fallback_to_pymupdf(self, mock_surya, mock_pymupdf, mock_docling):
        from app.document_processor import load_pdf
        mock_docling.side_effect = Exception("docling failed")
        mock_pymupdf.return_value = [{'page': 1, 'text': 'fallback text'}]
        result = load_pdf('/fake/path.pdf')
        assert result[0]['text'] == 'fallback text'
        mock_pymupdf.assert_called_once()


class TestLoadImage:
    @patch('app.document_processor.HAS_DOCLING', False)
    @patch('app.document_processor.HAS_SURYA', False)
    def test_basic_load_no_surya(self):
        from app.document_processor import load_image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (100, 50))
            img.save(f, format='JPEG')
            fname = f.name
        try:
            pages = load_image(fname)
            assert len(pages) == 1
            assert pages[0]['page'] == 1
            assert pages[0]['width'] == 100
            assert pages[0]['height'] == 50
            assert pages[0]['text'] == ''
        finally:
            os.unlink(fname)

    @patch('app.document_processor.HAS_DOCLING', False)
    @patch('app.document_processor.HAS_SURYA', True)
    @patch('app.document_processor._surya_ocr_image')
    def test_load_with_surya(self, mock_surya_ocr):
        from app.document_processor import load_image
        mock_surya_ocr.return_value = 'Surya OCR result'
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (100, 50))
            img.save(f, format='JPEG')
            fname = f.name
        try:
            pages = load_image(fname)
            assert pages[0]['text'] == 'Surya OCR result'
        finally:
            os.unlink(fname)

    @patch('app.document_processor.HAS_DOCLING', False)
    @patch('app.document_processor.HAS_SURYA', True)
    @patch('app.document_processor._surya_ocr_image')
    def test_surya_returns_empty_fallback(self, mock_surya_ocr):
        from app.document_processor import load_image
        mock_surya_ocr.return_value = ''
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (100, 50))
            img.save(f, format='JPEG')
            fname = f.name
        try:
            pages = load_image(fname)
            assert pages[0]['text'] == ''
        finally:
            os.unlink(fname)

    @patch('app.document_processor.HAS_DOCLING', False)
    @patch('app.document_processor.HAS_SURYA', True)
    @patch('app.document_processor._surya_ocr_image')
    def test_surya_exception_handled(self, mock_surya_ocr):
        from app.document_processor import load_image
        mock_surya_ocr.side_effect = RuntimeError("Surya error")
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (100, 50))
            img.save(f, format='JPEG')
            fname = f.name
        try:
            pages = load_image(fname)
            assert pages[0]['text'] == ''
        finally:
            os.unlink(fname)


class TestGetText:
    def test_single_page(self):
        from app.document_processor import get_text
        pages = [{'page': 1, 'text': 'Hello world'}]
        assert get_text(pages) == 'Hello world'

    def test_multi_page(self):
        from app.document_processor import get_text
        pages = [
            {'page': 1, 'text': 'Page one'},
            {'page': 2, 'text': 'Page two'},
        ]
        assert get_text(pages) == 'Page one\n\nPage two'

    def test_empty_pages_skipped(self):
        from app.document_processor import get_text
        pages = [
            {'page': 1, 'text': ''},
            {'page': 2, 'text': 'Only page two'},
        ]
        assert get_text(pages) == 'Only page two'

    def test_all_empty(self):
        from app.document_processor import get_text
        pages = [{'page': 1, 'text': ''}, {'page': 2, 'text': ''}]
        assert get_text(pages) == ''

    def test_empty_list(self):
        from app.document_processor import get_text
        assert get_text([]) == ''


class TestNormalizeText:
    def test_collapses_whitespace(self):
        from app.document_processor import normalize_text
        assert normalize_text('Hello    world\n\n\n  test') == 'Hello world test'

    def test_trims_edges(self):
        from app.document_processor import normalize_text
        assert normalize_text('  hello  ') == 'hello'

    def test_empty(self):
        from app.document_processor import normalize_text
        assert normalize_text('') == ''


class TestSupportedExtensions:
    def test_contains_pdf_and_jpg(self):
        from app.document_processor import supported_extensions
        exts = supported_extensions()
        assert '.pdf' in exts
        assert '.jpg' in exts
        assert '.jpeg' in exts

    def test_sorted_order(self):
        from app.document_processor import supported_extensions
        exts = supported_extensions()
        assert exts == sorted(exts)
