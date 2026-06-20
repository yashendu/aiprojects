import json
import re
import requests
import yaml

PROMPTS_PATH = '/app/prompts.yaml'

INDIC_UNICODE_RANGES = [
    (0x0900, 0x097F),  # Devanagari (Hindi, Sanskrit, Marathi, Nepali)
    (0x0980, 0x09FF),  # Bengali / Assamese
    (0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
    (0x0A80, 0x0AFF),  # Gujarati
    (0x0B00, 0x0B7F),  # Odia
    (0x0B80, 0x0BFF),  # Tamil
    (0x0C00, 0x0C7F),  # Telugu
    (0x0C80, 0x0CFF),  # Kannada
    (0x0D00, 0x0D7F),  # Malayalam
    (0x0D80, 0x0DFF),  # Sinhala
]


def load_prompts():
    with open(PROMPTS_PATH) as f:
        return yaml.safe_load(f)


def call_ollama(host, model, system, prompt, timeout=120, temperature=0.1, images=None, num_predict=8192):
    payload = {
        'model': model,
        'system': system,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': temperature,
            'num_predict': num_predict,
        },
    }
    if images:
        payload['images'] = images
    resp = requests.post(f'{host}/api/generate', json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()['response']


def is_indic_text(text):
    for char in text[:2000]:
        cp = ord(char)
        for start, end in INDIC_UNICODE_RANGES:
            if start <= cp <= end:
                return True
    return False


def _count_kv_patterns(text):
    count = 0
    for line in text.split('\n'):
        line = line.strip()
        colon = line.find(':')
        if colon > 0:
            label = line[:colon].strip()
            value = line[colon + 1:].strip()
            if label and value and len(label.split()) <= 4:
                count += 1
    return count


def check_extractable(host, model, text, config):
    text_sample = text[:3000]

    if _count_kv_patterns(text_sample) >= 1:
        return True, 'Document contains structured key-value pairs'

    prompts = load_prompts()
    p = prompts['prompts']['gibberish_v1']
    system = p['system']
    prompt = p['user_template'].format(document_text=text_sample.replace('\x00', ''))
    try:
        raw = call_ollama(host, model, system, prompt, temperature=0.0)
        data = _parse_json(raw)
        if data and isinstance(data, dict):
            is_ext = data.get('is_extractable', True)
            conf = data.get('confidence', 0.0)
            reason = data.get('reason', '')
            if not is_ext and conf >= 0.6:
                return False, reason
            return True, ''
    except Exception:
        pass
    return True, ''


def extract_pairs(host, model, text, config, similar_samples=None):
    prompts = load_prompts()
    p = prompts['prompts'].get('extraction_v2') or prompts['prompts']['extraction_v1']
    system = p['system']

    few_shot = ''
    if similar_samples:
        examples = []
        for s in similar_samples[:3]:
            pairs = s.get('extracted_pairs', [])
            if pairs:
                examples.append(json.dumps(pairs, indent=2))
        if examples:
            few_shot = 'Reference examples of similar extractions:\n' + '\n---\n'.join(examples)

    cleaned_text = text[:8000].replace('\x00', '')
    user_prompt = p['user_template'].format(
        document_text=cleaned_text,
        few_shot_examples=few_shot,
    )

    raw = call_ollama(host, model, system, user_prompt, temperature=0.1)
    data = _parse_json(raw)

    if data is None:
        fallback = _parse_text_pairs(raw)
        if fallback:
            return fallback, ''
        return [], f'Failed to parse LLM response. Raw: {raw[:200]}'

    if isinstance(data, dict) and 'error' in data:
        return [], data.get('reason', data['error'])

    if isinstance(data, list):
        validated = []
        for item in data:
            if isinstance(item, dict) and 'label' in item and 'value' in item:
                validated.append({
                    'label': str(item['label']).strip(),
                    'value': re.sub(r'^[$€£¥₹]+\s*', '', str(item['value']).strip()),
                })
        return validated, ''

    return [], 'Unexpected response format from LLM.'


def extract_indic_pairs(host, model, text, config, similar_samples=None):
    prompts = load_prompts()
    p = prompts['prompts']['extraction_indic_v1']
    system = p['system']

    few_shot = ''
    if similar_samples:
        examples = []
        for s in similar_samples[:3]:
            pairs = s.get('extracted_pairs', [])
            if pairs:
                examples.append(json.dumps(pairs, indent=2))
        if examples:
            few_shot = 'Reference examples of similar extractions:\n' + '\n---\n'.join(examples)

    cleaned_text = text[:8000].replace('\x00', '')
    user_prompt = p['user_template'].format(
        document_text=cleaned_text,
        few_shot_examples=few_shot,
    )

    raw = call_ollama(host, model, system, user_prompt, temperature=0.0, timeout=300, num_predict=8192)
    data = _parse_json(raw)

    if data is None:
        fallback = _parse_text_pairs(raw)
        if fallback:
            return fallback, ''
        return [], f'Failed to parse LLM response. Raw: {raw[:200]}'

    if isinstance(data, dict) and 'error' in data:
        return [], data.get('reason', data['error'])

    if isinstance(data, list):
        validated = []
        for item in data:
            if isinstance(item, dict) and 'label' in item and 'value' in item:
                validated.append({
                    'label': str(item['label']).strip(),
                    'value': str(item['value']).strip(),
                })
        return validated, ''

    return [], 'Unexpected response format from LLM.'


def validate_extraction(host, model, document_text, pairs):
    if not pairs:
        return pairs
    prompts = load_prompts()
    p = prompts['prompts'].get('extraction_validation_v1')
    if not p:
        return pairs
    system = p['system']
    cleaned_text = document_text[:6000].replace('\x00', '')
    user_prompt = p['user_template'].format(
        document_text=cleaned_text,
        extracted_json=json.dumps(pairs, indent=2),
    )
    try:
        raw = call_ollama(host, model, system, user_prompt, temperature=0.0, timeout=120)
        data = _parse_json(raw)
        if data and isinstance(data, dict) and 'validated_pairs' in data:
            validated = []
            for item in data['validated_pairs']:
                if isinstance(item, dict) and item.get('valid') and 'label' in item and 'value' in item:
                    validated.append({
                        'label': str(item['label']).strip(),
                        'value': str(item['value']).strip(),
                    })
            if validated:
                if len(validated) >= len(pairs) * 0.4:
                    for v in validated:
                        v['value'] = _strip_currency(v['value'])
                    return validated
    except Exception:
        pass
    return [{'label': p['label'], 'value': _strip_currency(p['value'])} for p in pairs]


def extract_text_from_image(host, model, image_path, config):
    import base64
    prompts = load_prompts()
    p = prompts['prompts']['image_analysis_v1']
    system = p['system']
    prompt = p['user_template']

    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()

    raw = call_ollama(host, model, system, prompt, timeout=120, images=[b64], num_predict=4096)
    data = _parse_json(raw)

    if data and isinstance(data, dict):
        if data.get('has_text'):
            return data['text'], ''
        return '', data.get('reason', 'No readable text found in the image.')
    return raw, ''


def _strip_currency(val):
    return re.sub(r'^[$€£¥₹]+\s*', '', val.strip())


def _parse_text_pairs(text):
    pairs = []
    seen_labels = set()
    for line in re.split(r'\n|\* ', text):
        line = line.strip().rstrip(',')
        if not line or line.startswith('**'):
            continue
        m = re.match(r'^[\*\-]\s*(.+?)\s*:\s*(.+)$', line)
        if not m:
            m = re.match(r'^(.+?)\s*:\s*(.+)$', line)
        if m:
            label = m.group(1).strip().rstrip('*').strip()
            value = _strip_currency(m.group(2))
            if label and value and len(label) < 80 and len(value) < 500:
                norm = label.lower()
                if norm not in seen_labels:
                    seen_labels.add(norm)
                    pairs.append({'label': label, 'value': value})
    return pairs if pairs else None


def _parse_json(text):
    text = text.strip()
    if not text:
        return None
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    text = text.replace('\x00', '')
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find('[')
    if start == -1:
        start = text.find('{')
    if start != -1:
        end = text.rfind(']') if text[start] == '[' else text.rfind('}')
        if end != -1 and end > start:
            candidate = text[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
            try:
                return json.loads(candidate + ('}' if text[start] == '{' else ']'))
            except json.JSONDecodeError:
                pass
    return None
