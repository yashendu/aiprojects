import builtins
import os
import sys
import tempfile
from unittest.mock import mock_open, patch
import pytest


@pytest.fixture(scope='package')
def tmp_app_dirs():
    uploads = tempfile.mkdtemp(prefix='app_uploads_')
    yield uploads
    import shutil
    shutil.rmtree(uploads, ignore_errors=True)


MOCK_CONFIG = """ollama:
  host: http://localhost:11434
  model: test-model
  vision_model: test-vision
  validation_model: test-validation
  indic_model: test-indic
generation:
  temperature: 0.1
  max_tokens: 4096
limits:
  max_upload_mb: 2
  max_image_pixels: 4096000
  supported_images: [.jpg, .jpeg]
  supported_docs: [.pdf]
learning:
  max_samples: 100
  similarity_top_k: 3
  store_path: /tmp/test_store
extraction:
  min_confidence: 0.3
  max_pairs: 50
"""

MOCK_PROMPTS_DATA = """prompts:
  extraction_v1:
    version: 1
    system: extract
    user_template: extract {document_text}
  gibberish_v1:
    version: 1
    system: check
    user_template: check {document_text}
  image_analysis_v1:
    version: 1
    system: analyze
    user_template: analyze
  extraction_indic_v1:
    version: 1
    system: extract indic
    user_template: extract {document_text} {few_shot_examples}
"""


@pytest.fixture(scope='package', autouse=True)
def mock_app_files(tmp_app_dirs):
    for mod in ['app.main', 'app.extractor', 'app.document_processor', 'app.learning_store']:
        if mod in sys.modules:
            del sys.modules[mod]

    _orig_open = builtins.open
    _orig_makedirs = os.makedirs
    _orig_path_exists = os.path.exists

    def _mock_open(path, *args, **kwargs):
        p = str(path)
        if p == '/app/config.yaml':
            return mock_open(read_data=MOCK_CONFIG).return_value
        if p == '/app/prompts.yaml':
            return mock_open(read_data=MOCK_PROMPTS_DATA).return_value
        if p.startswith('/app/static/uploads/'):
            relpath = p[len('/app/static/uploads/'):]
            real_path = os.path.join(tmp_app_dirs, relpath)
            return _orig_open(real_path, *args, **kwargs)
        return _orig_open(p, *args, **kwargs)

    def _mock_makedirs(path, mode=0o777, exist_ok=True):
        if path == '/app/static/uploads':
            _orig_makedirs(tmp_app_dirs, exist_ok=True)
            return
        if path.startswith('/app/'):
            return
        return _orig_makedirs(path, mode, exist_ok)

    def _mock_path_exists(path):
        if path.startswith('/app/'):
            return True
        return _orig_path_exists(path)

    with patch('builtins.open', side_effect=_mock_open):
        with patch('os.makedirs', side_effect=_mock_makedirs):
            with patch('os.path.exists', side_effect=_mock_path_exists):
                yield
