import os
import requests
from flask import Flask, request, jsonify, render_template, session
from app.document_loader import load_document, supported_extensions
from app.rag_engine import index_document, query_document, clear_document, load_config, load_precomputed, index_precomputed
from app.session_manager import sessions

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

CONFIG = load_config()
SAMPLE_PATH = CONFIG['sample']['path']
SAMPLE_URL = CONFIG['sample'].get('url', '')
PRECOMPUTED_PATH = CONFIG['sample'].get('precomputed')

GEN_CFG = CONFIG['generation']
OLLAMA_HOST = CONFIG['ollama']['host']
OLLAMA_MODEL = CONFIG['ollama']['model']

SYSTEM_TEMPLATE = """You are a helpful document assistant. Answer the user's question based ONLY on the provided document context below.

Rules:
- Answer ONLY using the document context. Do NOT use any external knowledge.
- If the answer is not in the context, say: "I'm sorry, I don't have information about that in the provided document. Could you ask something related to the document content?"
- Be empathetic, professional, and concise.
- Suggest follow-up questions that relate to what the document covers.

Document context:
{context}

Chat history:
{history}

User: {question}
Assistant:"""


OLLAMA_TIMEOUT = 120


def call_ollama(prompt):
    resp = requests.post(f'{OLLAMA_HOST}/api/generate', json={
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': GEN_CFG['temperature'],
            'top_p': GEN_CFG['top_p'],
            'num_predict': GEN_CFG['max_tokens'],
            'repeat_penalty': GEN_CFG['repeat_penalty'],
        },
    }, timeout=OLLAMA_TIMEOUT)
    resp.raise_for_status()
    return resp.json()['response']


def get_suggestions(context):
    prompt = (
        "Based on the following document content, suggest exactly 3 brief, "
        "specific questions a user might ask. Return them as a JSON array of strings, "
        "nothing else.\n\nDocument:\n" + context[:2000]
    )
    try:
        resp = call_ollama(prompt)
        import json
        suggestions = json.loads(resp)
        if isinstance(suggestions, list):
            return suggestions[:5]
    except Exception:
        pass
    return []


@app.route('/')
def index():
    return render_template('index.html',
                           max_lines=CONFIG['limits']['max_paste_lines'])


def auto_load_sample(sid):
    if not PRECOMPUTED_PATH or not os.path.exists(PRECOMPUTED_PATH):
        return False, []
    if not os.path.exists(SAMPLE_PATH):
        return False, []
    try:
        precomputed = load_precomputed(PRECOMPUTED_PATH)
        n = index_precomputed(sid, precomputed, CONFIG)
        sessions.set_document(sid, os.path.basename(SAMPLE_PATH))
        url_part = f" You can also download and read the document at {SAMPLE_URL}" if SAMPLE_URL else ""
        msg = f"For demo purpose: A sample HR policy loaded ({n} sections indexed). Ask me anything about it.{url_part}"
        sessions.add_message(sid, 'assistant', msg)
        faqs = precomputed.get('faqs', [])
        return True, faqs
    except Exception:
        return False, []


@app.route('/api/start', methods=['POST'])
def start_session():
    sid = sessions.create()
    session['sid'] = sid
    greeting = "Hello! I'm your document assistant."
    sessions.add_message(sid, 'assistant', greeting)
    _, faqs = auto_load_sample(sid)
    return jsonify({'session_id': sid, 'messages': sessions.get_history(sid), 'suggestions': faqs})


@app.route('/api/upload', methods=['POST'])
def upload():
    sid = session.get('sid')
    if not sid or not sessions.get(sid):
        return jsonify({'error': 'No session'}), 400

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

    tmp = f'/tmp/{os.urandom(8).hex()}_{file.filename}'
    file.save(tmp)
    try:
        text = load_document(tmp)
        if not text.strip():
            raise ValueError('File appears to be empty or unreadable.')
        clear_document(sid)
        sessions.clear(sid)
        sid = sessions.create()
        session['sid'] = sid
        n = index_document(text, sid, CONFIG)
        sessions.set_document(sid, file.filename)
        msg = f'Document "{file.filename}" loaded ({n} sections indexed). You can now ask questions.'
        sessions.add_message(sid, 'assistant', msg)
        suggestions = get_suggestions(text)
        return jsonify({'message': f'Document indexed: {n} sections', 'messages': sessions.get_history(sid), 'suggestions': suggestions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


@app.route('/api/paste', methods=['POST'])
def paste():
    sid = session.get('sid')
    if not sid or not sessions.get(sid):
        return jsonify({'error': 'No session'}), 400

    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = data['text'].strip()
    lines = text.split('\n')
    max_lines = CONFIG['limits']['max_paste_lines']
    if len(lines) > max_lines:
        return jsonify({'error': f'Text exceeds {max_lines} line limit ({len(lines)} lines).'}), 400

    if not text:
        return jsonify({'error': 'Empty text provided.'}), 400

    try:
        clear_document(sid)
        sessions.clear(sid)
        sid = sessions.create()
        session['sid'] = sid
        n = index_document(text, sid, CONFIG)
        sessions.set_document(sid, 'pasted_text.txt')
        msg = f'Pasted text loaded ({n} sections indexed). You can now ask questions.'
        sessions.add_message(sid, 'assistant', msg)
        suggestions = get_suggestions(text)
        return jsonify({'message': f'Text indexed: {n} sections', 'messages': sessions.get_history(sid), 'suggestions': suggestions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    sid = session.get('sid')
    if not sid or not sessions.get(sid):
        return jsonify({'error': 'No session. Please refresh.'}), 400

    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'No question'}), 400

    question = data['question'].strip()
    if not question:
        return jsonify({'error': 'Empty question'}), 400

    sessions.add_message(sid, 'user', question)

    chunks = query_document(question, sid, CONFIG)
    if not chunks:
        response = "I don't have any document loaded yet. Please upload a document or paste text to get started."
        sessions.add_message(sid, 'assistant', response)
        history = sessions.get_history(sid)
        return jsonify({'response': response, 'messages': history})

    context = '\n\n'.join(chunks)
    history_text = '\n'.join(f"{m['role']}: {m['text']}" for m in sessions.get_history(sid)[-6:-1])

    prompt = SYSTEM_TEMPLATE.format(context=context, history=history_text, question=question)

    try:
        response = call_ollama(prompt)
    except requests.Timeout:
        response = "I'm sorry, the request timed out. The model is taking too long to respond. Please try a simpler question."
    except requests.ConnectionError:
        response = "I'm sorry, I can't reach the AI model. Please check that Ollama is running and try again."
    except Exception as e:
        response = f"I'm sorry, an error occurred: {str(e)}"

    sessions.add_message(sid, 'assistant', response)
    history = sessions.get_history(sid)

    suggestions = get_suggestions(context) if len(history) < 4 else []

    return jsonify({'response': response, 'messages': history, 'suggestions': suggestions})


@app.route('/api/restart', methods=['POST'])
def restart():
    old_sid = session.get('sid')
    if old_sid:
        clear_document(old_sid)
        sessions.clear(old_sid)
    sid = sessions.create()
    session['sid'] = sid
    greeting = "Hello! I'm your document assistant."
    sessions.add_message(sid, 'assistant', greeting)
    _, faqs = auto_load_sample(sid)
    return jsonify({'session_id': sid, 'messages': sessions.get_history(sid), 'suggestions': faqs})
