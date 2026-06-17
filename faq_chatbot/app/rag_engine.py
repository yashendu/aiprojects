import os
import requests
import chromadb
from chromadb.config import Settings
import yaml


def load_config():
    with open('/app/config.yaml') as f:
        return yaml.safe_load(f)


OLLAMA_EMBED_TIMEOUT = 120


def embed_texts(texts, config):
    host = config['ollama']['host']
    model = config['ollama']['embedding_model']
    resp = requests.post(f'{host}/api/embed', json={
        'model': model,
        'input': texts,
    }, timeout=OLLAMA_EMBED_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data['embeddings']


def chunk_text(text, chunk_size, chunk_overlap):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(' '.join(words[start:end]))
        start += chunk_size - chunk_overlap
    return chunks


COLLECTION_PREFIX = 'faq_doc_'


def get_collection_path(session_id):
    return f'/app/chroma/{session_id}'


def index_document(text, session_id, config):
    c = config['chunking']
    chunks = chunk_text(text, c['chunk_size'], c['chunk_overlap'])
    if not chunks:
        return 0

    path = get_collection_path(session_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    client = chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False))
    collection = client.get_or_create_collection(COLLECTION_PREFIX + session_id)

    existing = collection.count()
    if existing > 0:
        client.delete_collection(COLLECTION_PREFIX + session_id)
        collection = client.get_or_create_collection(COLLECTION_PREFIX + session_id)

    embeddings = embed_texts(chunks, config)
    ids = [f'{session_id}_{i}' for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
    )
    return len(chunks)


def query_document(question, session_id, config):
    path = get_collection_path(session_id)
    if not os.path.exists(path):
        return []

    client = chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False))
    collection = client.get_collection(COLLECTION_PREFIX + session_id)

    q_emb = embed_texts([question], config)
    results = collection.query(query_embeddings=q_emb, n_results=config['chunking']['top_k'])

    if not results['documents'] or not results['documents'][0]:
        return []

    return results['documents'][0]


def clear_document(session_id):
    path = get_collection_path(session_id)
    if os.path.exists(path):
        import shutil
        shutil.rmtree(path)
