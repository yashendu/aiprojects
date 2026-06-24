"""
Integration tests with Hindi sample documents using Surya OCR.

Run inside Docker after building:
  pip install -r requirements.txt
  python tests/generate_hindi_samples.py
  docker compose exec -T i-extract python -m pytest tests/test_hindi_extraction.py -v
"""
import os
import json
import io
import sys

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


def _get_expected_labels(name):
    labels_map = {
        'invoice': ['Invoice Number', 'Date', 'Seller Name', 'Buyer Name', 'Total Amount', 'Item'],
        'identity': ['Name', 'Father Name', 'Address', 'Date of Birth', 'ID Number', 'Blood Group'],
        'form': ['Applicant Name', 'Father Name', 'Date of Birth', 'Mobile Number', 'Email', 'Position'],
        'receipt': ['Receipt Number', 'Date', 'Recipient', 'Amount', 'Payment Method', 'Reason'],
        'contract': ['Contract Number', 'Date', 'First Party', 'Second Party', 'Project', 'Contract Amount'],
    }
    return labels_map.get(name, [])


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
        assert len(lang_events) == 1, f'Missing language_detected event for {name}'
        assert lang_events[0]['language'] == 'Hindi', f'{name}: expected Hindi, got {lang_events[0]["language"]}'
        complete = [e for e in events if e.get('stage') == 'complete']
        assert len(complete) == 1, f'Missing complete event for {name}'
        assert complete[0].get('document_html', ''), f'{name}: missing document_html'


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
        assert len(lang_events) == 1, f'Missing language_detected event for {name} PDF'
        assert lang_events[0]['language'] == 'Hindi', f'{name} PDF: expected Hindi, got {lang_events[0]["language"]}'
        complete = [e for e in events if e.get('stage') == 'complete']
        assert len(complete) == 1, f'Missing complete event for {name} PDF'
        assert complete[0].get('document_html', ''), f'{name} PDF: missing document_html'


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
        assert lang[0]['confidence'] >= 0.5, f'Low confidence: {lang[0]}'

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
        assert lang[0]['confidence'] >= 0.5


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
        assert lang[0]['language'] == 'English', f'Expected English, got {lang[0]}'
