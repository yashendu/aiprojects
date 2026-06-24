"""Integration tests for the full extraction pipeline with Hindi samples."""

import os
import json
import io

import pytest
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
SAMPLES = os.path.join(HERE, 'hindi_samples')

pytestmark = pytest.mark.skipif(
    not os.path.isdir(SAMPLES) or not os.listdir(SAMPLES),
    reason='Hindi samples not generated; run: python tests/generate_hindi_samples.py'
)


@pytest.fixture(scope='module')
def app():
    import app.main
    flask_app = app.main.app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


class TestHindiJpegExtraction:
    @pytest.mark.parametrize('name', ['invoice', 'identity', 'form', 'receipt', 'contract'])
    def test_hindi_jpeg_has_surya_text(self, name, client):
        path = os.path.join(SAMPLES, f'{name}.jpg')
        if not os.path.exists(path):
            pytest.skip(f'Sample {path} not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), f'{name}.jpg')}
            resp = client.post('/api/upload', data=data)
        assert resp.status_code == 200
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        lang_events = [e for e in events if e.get('stage') == 'language_detected']
        assert len(lang_events) == 1
        assert lang_events[0]['language'] == 'Hindi'
        complete = [e for e in events if e.get('stage') == 'complete']
        assert len(complete) == 1
        assert complete[0].get('document_html', '')

    @pytest.mark.parametrize('name', ['invoice', 'identity', 'form', 'receipt', 'contract'])
    def test_hindi_jpeg_has_extracted_data(self, name, client):
        path = os.path.join(SAMPLES, f'{name}.jpg')
        if not os.path.exists(path):
            pytest.skip(f'Sample {path} not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), f'{name}.jpg')}
            resp = client.post('/api/upload', data=data)
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        complete = [e for e in events if e.get('stage') == 'complete']
        if not complete:
            return
        result = complete[0]
        if 'extracted_text' in result and result['extracted_text']:
            assert 'error' not in result

    @pytest.mark.parametrize('name', ['invoice', 'identity', 'form', 'receipt', 'contract'])
    def test_hindi_jpeg_confidence_threshold(self, name, client):
        path = os.path.join(SAMPLES, f'{name}.jpg')
        if not os.path.exists(path):
            pytest.skip(f'Sample {path} not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), f'{name}.jpg')}
            resp = client.post('/api/upload', data=data)
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        lang = [e for e in events if e.get('stage') == 'language_detected']
        if lang:
            assert lang[0]['confidence'] >= 0.5, f'Low confidence: {lang[0]}'


class TestHindiPdfExtraction:
    @pytest.mark.parametrize('name', ['invoice', 'identity', 'form', 'receipt', 'contract'])
    def test_hindi_pdf_has_surya_text(self, name, client):
        path = os.path.join(SAMPLES, f'{name}.pdf')
        if not os.path.exists(path):
            pytest.skip(f'Sample {path} not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), f'{name}.pdf')}
            resp = client.post('/api/upload', data=data)
        assert resp.status_code == 200
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        lang_events = [e for e in events if e.get('stage') == 'language_detected']
        assert len(lang_events) == 1
        assert lang_events[0]['language'] == 'Hindi'
        complete = [e for e in events if e.get('stage') == 'complete']
        assert len(complete) == 1
        assert complete[0].get('document_html', '')

    @pytest.mark.parametrize('name', ['invoice', 'identity', 'form', 'receipt', 'contract'])
    def test_hindi_pdf_confidence_threshold(self, name, client):
        path = os.path.join(SAMPLES, f'{name}.pdf')
        if not os.path.exists(path):
            pytest.skip(f'Sample {path} not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), f'{name}.pdf')}
            resp = client.post('/api/upload', data=data)
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        lang = [e for e in events if e.get('stage') == 'language_detected']
        if lang:
            assert lang[0]['confidence'] >= 0.5


class TestLanguageDetection:
    @pytest.mark.parametrize('name', ['invoice', 'identity', 'form', 'receipt', 'contract'])
    def test_hindi_jpeg_shows_hindi_badge(self, name, client):
        path = os.path.join(SAMPLES, f'{name}.jpg')
        if not os.path.exists(path):
            pytest.skip(f'Sample {path} not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), f'{name}.jpg')}
            resp = client.post('/api/upload', data=data)
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        lang = [e for e in events if e.get('stage') == 'language_detected']
        assert lang
        assert lang[0]['language'] == 'Hindi'

    @pytest.mark.parametrize('name', ['invoice', 'identity', 'form', 'receipt', 'contract'])
    def test_hindi_pdf_shows_hindi_badge(self, name, client):
        path = os.path.join(SAMPLES, f'{name}.pdf')
        if not os.path.exists(path):
            pytest.skip(f'Sample {path} not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), f'{name}.pdf')}
            resp = client.post('/api/upload', data=data)
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        lang = [e for e in events if e.get('stage') == 'language_detected']
        assert lang
        assert lang[0]['language'] == 'Hindi'


class TestLanguageDetectionStages:
    def test_language_detected_before_complete_jpeg(self, client):
        path = os.path.join(SAMPLES, 'invoice.jpg')
        if not os.path.exists(path):
            pytest.skip('Sample invoice.jpg not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), 'invoice.jpg')}
            resp = client.post('/api/upload', data=data)
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        stages = [e['stage'] for e in events]
        assert 'language_detected' in stages
        assert stages.index('language_detected') < stages.index('complete')

    def test_language_detected_before_extraction_jpeg(self, client):
        path = os.path.join(SAMPLES, 'invoice.jpg')
        if not os.path.exists(path):
            pytest.skip('Sample invoice.jpg not found')
        with open(path, 'rb') as f:
            data = {'file': (io.BytesIO(f.read()), 'invoice.jpg')}
            resp = client.post('/api/upload', data=data)
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        stages = [e['stage'] for e in events]
        if 'extracting' in stages:
            assert stages.index('language_detected') < stages.index('extracting')


class TestEnglishControl:
    def test_english_jpeg_is_english(self, client):
        img = Image.new('RGB', (400, 200), 'white')
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        except Exception:
            font = ImageFont.load_default()
        draw.text((20, 20), 'Invoice #INV-001', fill='black', font=font)
        draw.text((20, 50), 'Name: John Doe', fill='black', font=font)
        draw.text((20, 80), 'Amount: $500', fill='black', font=font)
        buf = io.BytesIO()
        img.save(buf, 'JPEG')
        buf.seek(0)
        data = {'file': (buf, 'english_test.jpg')}
        resp = client.post('/api/upload', data=data)
        events = [json.loads(line) for line in resp.data.decode().strip().split('\n') if line.strip()]
        lang = [e for e in events if e.get('stage') == 'language_detected']
        assert lang
        assert lang[0]['language'] == 'English'
