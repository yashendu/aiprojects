from PIL import Image

try:
    from surya.ocr import run_ocr
    from surya.model.recognition.model import load_model as load_recognition_model
    from surya.model.recognition.processor import load_processor as load_recognition_processor
    from surya.model.detection.model import load_model as load_detection_model
    from surya.model.detection.model import load_processor as load_detection_processor
    HAS_SURYA = True
except ImportError:
    HAS_SURYA = False

_det_model = None
_det_processor = None
_rec_model = None
_rec_processor = None

_INDIC_LANGS = ["hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or", "si", "en"]


def _get_models():
    global _det_model, _det_processor, _rec_model, _rec_processor
    if _det_model is None:
        _det_model = load_detection_model()
        _det_processor = load_detection_processor()
        _rec_model = load_recognition_model()
        _rec_processor = load_recognition_processor()
    return _det_model, _det_processor, _rec_model, _rec_processor


def _extract_text(predictions):
    lines = []
    for pred in predictions:
        for line in pred.text_lines:
            t = line.text.strip()
            if t:
                lines.append(t)
    return '\n'.join(lines)


def ocr_image(image, langs=None):
    if not HAS_SURYA:
        return None
    if langs is None:
        langs = _INDIC_LANGS
    det_model, det_processor, rec_model, rec_processor = _get_models()
    if isinstance(image, str):
        image = Image.open(image)
    predictions = run_ocr([image], [langs], det_model, det_processor, rec_model, rec_processor)
    return _extract_text(predictions)


def ocr_images(images, langs=None):
    if not HAS_SURYA:
        return [None] * len(images)
    if langs is None:
        langs = _INDIC_LANGS
    det_model, det_processor, rec_model, rec_processor = _get_models()
    loaded = []
    for img in images:
        if isinstance(img, str):
            loaded.append(Image.open(img))
        else:
            loaded.append(img)
    predictions = run_ocr(loaded, [langs] * len(loaded), det_model, det_processor, rec_model, rec_processor)
    results = []
    for pred in predictions:
        lines = []
        for line in pred.text_lines:
            t = line.text.strip()
            if t:
                lines.append(t)
        results.append('\n'.join(lines))
    return results
