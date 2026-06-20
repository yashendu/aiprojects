import os
import re
import io
import csv
import json
import uuid
from flask import Flask, request, jsonify, render_template, session, send_file, stream_with_context, Response
from app.document_processor import load_pdf, load_image, get_text, render_document_html, normalize_text, supported_extensions, SUPPORTED_DOCS, SUPPORTED_IMAGES
from app.extractor import extract_pairs, extract_indic_pairs, check_extractable, extract_text_from_image, validate_extraction, load_prompts, is_indic_text, _count_kv_patterns
from app.learning_store import LearningStore
import yaml

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = '/app/static/uploads'

with open('/app/config.yaml') as f:
    CONFIG = yaml.safe_load(f)

OLLAMA_HOST = CONFIG['ollama']['host']
OLLAMA_MODEL = CONFIG['ollama']['model']
VISION_MODEL = CONFIG['ollama']['vision_model']
VALIDATION_MODEL = CONFIG['ollama'].get('validation_model', OLLAMA_MODEL)
INDIC_MODEL = CONFIG['ollama'].get('indic_model', OLLAMA_MODEL)
GEN_CFG = CONFIG['generation']

learning_store = LearningStore(
    store_path=CONFIG['learning']['store_path'],
    max_samples=CONFIG['learning']['max_samples'],
    similarity_top_k=CONFIG['learning']['similarity_top_k'],
)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html',
                           max_mb=CONFIG['limits']['max_upload_mb'],
                           model_label=OLLAMA_MODEL,
                           vision_label=VISION_MODEL,
                           validation_label=VALIDATION_MODEL,
                           indic_label=INDIC_MODEL)


def _emit(event):
    return json.dumps(event) + '\n'

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in supported_extensions():
        return jsonify({'error': f'Unsupported file type: {ext}. Supported: {", ".join(supported_extensions())}'}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > CONFIG['limits']['max_upload_mb'] * 1024 * 1024:
        return jsonify({'error': f'File exceeds {CONFIG["limits"]["max_upload_mb"]}MB limit'}), 400

    upload_id = uuid.uuid4().hex[:12]
    fname = f'{upload_id}_{file.filename}'
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    file.save(save_path)

    def generate():
        try:
            yield _emit({'stage': 'parsing', 'message': 'Parsing document...'})

            if ext in SUPPORTED_DOCS:
                yield _emit({'stage': 'parsing', 'message': f'Feeding PDF to {OLLAMA_MODEL}...'})
                pages = load_pdf(save_path)
                document_text = get_text(pages)
            elif ext in SUPPORTED_IMAGES:
                yield _emit({'stage': 'parsing', 'message': f'Scanning image with {VISION_MODEL}...'})
                pages = load_image(save_path)
                image_text, img_err = extract_text_from_image(OLLAMA_HOST, VISION_MODEL, save_path, CONFIG)
                if img_err:
                    document_text = ''
                else:
                    document_text = image_text
                if pages and pages[0].get('image_path'):
                    pages[0]['text'] = document_text
            else:
                yield _emit({'stage': 'error', 'message': 'Unsupported file type.'})
                return

            raw_text = document_text
            document_text = normalize_text(document_text)

            if not document_text.strip():
                doc_html = render_document_html(pages)
                yield _emit({'stage': 'complete', 'extracted': [], 'document_html': doc_html, 'message': 'No readable text could be extracted from this file.'})
                return

            kv_pattern_count = _count_kv_patterns(raw_text)

            yield _emit({'stage': 'analyzing', 'message': 'Checking if document contains structured data...'})
            is_extractable, reason = check_extractable(OLLAMA_HOST, OLLAMA_MODEL, document_text, CONFIG)

            if not is_extractable:
                doc_html = render_document_html(pages)
                yield _emit({'stage': 'complete', 'extracted': [], 'document_html': doc_html, 'message': f'No extractable key-value pairs found. {reason}'})
                return

            if is_indic_text(document_text):
                extract_model = INDIC_MODEL
                extract_fn = extract_indic_pairs
                extract_label = INDIC_MODEL
            else:
                extract_model = OLLAMA_MODEL
                extract_fn = extract_pairs
                extract_label = OLLAMA_MODEL

            yield _emit({'stage': 'extracting', 'message': f'Hunting for key-value pairs with {extract_label}...'})
            similar = learning_store.get_similar_samples(document_text)
            extracted, err = extract_fn(OLLAMA_HOST, extract_model, document_text, CONFIG, similar)

            if err:
                doc_html = render_document_html(pages)
                yield _emit({'stage': 'complete', 'extracted': [], 'document_html': doc_html, 'message': err})
                return

            if not extracted:
                doc_html = render_document_html(pages)
                yield _emit({'stage': 'complete', 'extracted': [], 'document_html': doc_html, 'message': 'The document was analyzed but no key-value pairs could be identified.'})
                return

            if kv_pattern_count == 0:
                extracted = []

            if extracted and VALIDATION_MODEL != OLLAMA_MODEL:
                yield _emit({'stage': 'validating', 'message': f'Validating extraction with {VALIDATION_MODEL}...'})
                validated = validate_extraction(OLLAMA_HOST, VALIDATION_MODEL, document_text, extracted)
                if validated:
                    stripped_count = len(extracted) - len(validated)
                    extracted = validated
                    if stripped_count:
                        validation_msg = f'{len(extracted)} fields extracted ({stripped_count} hallucinated values flagged by {VALIDATION_MODEL}).'
                    else:
                        validation_msg = f'All {len(extracted)} fields verified by {VALIDATION_MODEL}.'
                else:
                    validation_msg = f'Successfully extracted {len(extracted)} fields.'
            elif extracted:
                validation_msg = f'Successfully extracted {len(extracted)} fields.'
            else:
                validation_msg = 'The document was analyzed but no key-value pairs could be identified.'

            learning_store.save_sample(file.filename, document_text, extracted, OLLAMA_MODEL)

            doc_html = render_document_html(pages)
            yield _emit({'stage': 'complete', 'extracted': extracted, 'document_html': doc_html, 'message': validation_msg})

        except Exception as e:
            yield _emit({'stage': 'error', 'message': str(e)})
        finally:
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except OSError:
                    pass

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')


@app.route('/api/export_csv', methods=['POST'])
def export_csv():
    data = request.get_json()
    if not data or 'rows' not in data:
        return jsonify({'error': 'No data provided'}), 400

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Serial No.', 'Label', 'Value'])
    for i, row in enumerate(data['rows'], 1):
        writer.writerow([i, row.get('label', ''), row.get('value', '')])

    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='extracted_data.csv')


@app.route('/api/learning/stats', methods=['GET'])
def learning_stats():
    return jsonify({'sample_count': learning_store.count()})


@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    prompts = load_prompts()
    return jsonify(prompts)
