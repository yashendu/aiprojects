import json
import io
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image


MOCK_CONFIG = {
    'ollama': {
        'host': 'http://localhost:11434',
        'model': 'test-model',
        'vision_model': 'test-vision',
        'validation_model': 'test-validation',
        'indic_model': 'test-indic',
    },
    'generation': {'temperature': 0.1, 'top_p': 0.9, 'max_tokens': 4096, 'repeat_penalty': 1.1},
    'limits': {'max_upload_mb': 2, 'max_image_pixels': 4096000, 'supported_images': ['.jpg', '.jpeg'], 'supported_docs': ['.pdf']},
    'learning': {'max_samples': 100, 'similarity_top_k': 3, 'store_path': '/tmp/test_store'},
    'extraction': {'min_confidence': 0.3, 'max_pairs': 50},
    'surya': {'enabled': True, 'languages': ['hi', 'en']},
}

MOCK_PROMPTS = {
    'prompts': {
        'extraction_v1': {'version': 1, 'system': 'extract', 'user_template': 'extract {document_text}'},
        'gibberish_v1': {'version': 1, 'system': 'check', 'user_template': 'check {document_text}'},
        'image_analysis_v1': {'version': 1, 'system': 'analyze', 'user_template': 'analyze'},
        'extraction_indic_v1': {'version': 1, 'system': 'extract indic', 'user_template': 'extract {document_text}'},
    }
}


@pytest.fixture(autouse=True)
def mock_deps():
    with patch('yaml.safe_load', return_value=MOCK_CONFIG):
        with patch('app.main.load_prompts', return_value=MOCK_PROMPTS):
            with patch('app.learning_store.LearningStore.save_sample'):
                with patch('app.learning_store.LearningStore.get_similar_samples', return_value=[]):
                    with patch('app.learning_store.LearningStore.count', return_value=0):
                        from app.main import app as flask_app
                        flask_app.config['TESTING'] = True
                        ctx = flask_app.app_context()
                        ctx.push()
                        yield flask_app
                        ctx.pop()


@pytest.fixture
def client(mock_deps):
    return mock_deps.test_client()


class TestUploadAPI:
    def test_no_file(self, client):
        resp = client.post('/api/upload')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_empty_filename(self, client):
        resp = client.post('/api/upload', data={'file': (io.BytesIO(b''), '')})
        assert resp.status_code == 400

    def test_unsupported_extension(self, client):
        data = {'file': (io.BytesIO(b'hello'), 'test.txt')}
        resp = client.post('/api/upload', data=data)
        assert resp.status_code == 400

    def test_file_too_large(self, client):
        big = io.BytesIO(b'x' * (3 * 1024 * 1024))
        data = {'file': (big, 'test.pdf')}
        resp = client.post('/api/upload', data=data)
        assert resp.status_code == 413


class TestSSELanguageDetection:
    @patch('app.main.load_pdf')
    @patch('app.main.check_extractable')
    @patch('app.main._count_kv_patterns')
    def test_emits_language_detected_for_pdf(self, mock_kv, mock_check, mock_load_pdf, client):
        mock_load_pdf.return_value = [{'page': 1, 'text': 'Hello world this is an English document'}]
        mock_kv.return_value = 0
        mock_check.return_value = (False, 'No extractable data')

        data = {'file': (io.BytesIO(b'%PDF-1.4 fake'), 'test.pdf')}
        resp = client.post('/api/upload', data=data)
        assert resp.status_code == 200

        events = []
        for line in resp.data.decode().strip().split('\n'):
            if line.strip():
                events.append(json.loads(line))

        lang_events = [e for e in events if e.get('stage') == 'language_detected']
        assert len(lang_events) == 1
        assert lang_events[0]['language'] == 'English'
        assert lang_events[0]['confidence'] > 0

    @patch('app.main.load_image')
    @patch('app.main.check_extractable')
    @patch('app.main._count_kv_patterns')
    def test_emits_language_detected_for_hindi_image(self, mock_kv, mock_check, mock_load_image, client):
        mock_load_image.return_value = [{'page': 1, 'text': 'नमस्ते दुनिया यह हिंदी में है', 'image_path': None}]
        mock_kv.return_value = 0
        mock_check.return_value = (False, 'No extractable data')

        data = {'file': (io.BytesIO(b'fake-image-data'), 'test.jpg')}
        resp = client.post('/api/upload', data=data)

        assert resp.status_code == 200
        events = []
        for line in resp.data.decode().strip().split('\n'):
            if line.strip():
                events.append(json.loads(line))

        lang_events = [e for e in events if e.get('stage') == 'language_detected']
        assert len(lang_events) == 1
        assert lang_events[0]['language'] == 'Hindi'
        assert lang_events[0]['confidence'] > 0.5

    @patch('app.main.load_pdf')
    @patch('app.main.check_extractable')
    @patch('app.main._count_kv_patterns')
    def test_language_detected_before_complete(self, mock_kv, mock_check, mock_load_pdf, client):
        mock_load_pdf.return_value = [{'page': 1, 'text': 'Some text'}]
        mock_kv.return_value = 0
        mock_check.return_value = (False, 'Not extractable')

        data = {'file': (io.BytesIO(b'%PDF-1.4 fake'), 'test.pdf')}
        resp = client.post('/api/upload', data=data)
        events = []
        for line in resp.data.decode().strip().split('\n'):
            if line.strip():
                events.append(json.loads(line))

        stages = [e['stage'] for e in events]
        assert 'language_detected' in stages
        assert stages.index('language_detected') < stages.index('complete')


class TestExportCSV:
    def test_export_valid(self, client):
        resp = client.post('/api/export_csv', json={
            'rows': [{'label': 'Name', 'value': 'John'}, {'label': 'Age', 'value': '30'}]
        })
        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'
        content = resp.data.decode()
        assert 'Name' in content
        assert 'John' in content
        assert 'Age' in content

    def test_export_no_data(self, client):
        resp = client.post('/api/export_csv', json={})
        assert resp.status_code == 400

    def test_export_empty_rows(self, client):
        resp = client.post('/api/export_csv', json={'rows': []})
        assert resp.status_code == 200


class TestLearningStats:
    def test_stats_endpoint(self, client):
        resp = client.get('/api/learning/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'sample_count' in data


class TestPrompts:
    def test_prompts_endpoint(self, client):
        resp = client.get('/api/prompts')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'prompts' in data


class TestIndex:
    def test_index_returns_html(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'i_extract' in resp.data
