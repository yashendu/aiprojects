import sys, os
sys.path.insert(0, '/app')
from app.rag_engine import load_config, precompute_embeddings
from app.document_loader import load_document

config = load_config()
sample_path = config['sample']['path']
precomputed_path = config['sample']['precomputed']

if not os.path.exists(sample_path):
    print(f"Sample not found: {sample_path}")
    sys.exit(1)

if os.path.exists(precomputed_path):
    print(f"Precomputed embeddings already exist at {precomputed_path}")
    sys.exit(0)

print("Loading sample document...")
text = load_document(sample_path)
print(f"Loaded {len(text)} characters, {len(text.split())} words")

print("Computing embeddings and FAQs. This may take a while...")
n, faqs = precompute_embeddings(text, config, precomputed_path)
print(f"Done. {n} chunks saved to {precomputed_path}")
if faqs:
    print(f"Generated {len(faqs)} FAQ suggestions:")
    for f in faqs:
        print(f"  - {f}")
else:
    print("No FAQs generated.")
