import json
import os
import uuid


class LearningStore:
    def __init__(self, store_path, max_samples=100, similarity_top_k=3):
        self.store_path = store_path
        self.max_samples = max_samples
        self.similarity_top_k = similarity_top_k
        os.makedirs(store_path, exist_ok=True)

    def save_sample(self, filename, document_text, extracted_pairs, model_used):
        sample = {
            'id': uuid.uuid4().hex[:12],
            'filename': filename,
            'document_text': document_text[:5000],
            'extracted_pairs': extracted_pairs,
            'model_used': model_used,
            'pair_count': len(extracted_pairs),
        }
        path = os.path.join(self.store_path, f'{sample["id"]}.json')
        with open(path, 'w') as f:
            json.dump(sample, f, indent=2)
        self._trim()
        return sample['id']

    def get_similar_samples(self, document_text, top_k=None):
        k = top_k or self.similarity_top_k
        samples = self._load_all()
        if not samples:
            return []

        doc_words = set(document_text.lower().split())
        scored = []
        for s in samples:
            sample_words = set(s.get('document_text', '').lower().split())
            if not sample_words:
                continue
            overlap = len(doc_words & sample_words)
            scored.append((overlap, s))

        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored[:k] if _ > 0]

    def _load_all(self):
        samples = []
        if not os.path.isdir(self.store_path):
            return samples
        for fname in sorted(os.listdir(self.store_path)):
            if fname.endswith('.json'):
                try:
                    with open(os.path.join(self.store_path, fname)) as f:
                        samples.append(json.load(f))
                except (json.JSONDecodeError, OSError):
                    continue
        return samples

    def _trim(self):
        samples = self._load_all()
        if len(samples) <= self.max_samples:
            return
        samples.sort(key=lambda s: s.get('pair_count', 0), reverse=True)
        keep = {s['id'] for s in samples[:self.max_samples]}
        for fname in os.listdir(self.store_path):
            if fname.endswith('.json'):
                sid = fname.replace('.json', '')
                if sid not in keep:
                    try:
                        os.remove(os.path.join(self.store_path, fname))
                    except OSError:
                        pass

    def count(self):
        return len(self._load_all())
