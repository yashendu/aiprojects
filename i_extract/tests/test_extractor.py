import pytest
from app.extractor import (
    detect_document_language,
    is_indic_text,
    _count_kv_patterns,
    _count_scripts,
    _parse_json,
    _strip_currency,
)


class TestDetectDocumentLanguage:
    def test_english_text(self):
        text = "The quick brown fox jumps over the lazy dog. Hello world!"
        result = detect_document_language(text)
        assert result['language'] == 'English'
        assert result['confidence'] > 0.5

    def test_hindi_text(self):
        text = "नमस्ते दुनिया। यह एक हिंदी पाठ है। आप कैसे हैं?"
        result = detect_document_language(text)
        assert result['language'] == 'Hindi'
        assert result['confidence'] > 0.5

    def test_tamil_text(self):
        text = "வணக்கம் உலகம். இது ஒரு தமிழ் உரை."
        result = detect_document_language(text)
        assert result['language'] == 'Tamil'
        assert result['confidence'] > 0.5

    def test_bengali_text(self):
        text = "নমস্কার বিশ্ব। এটি একটি বাংলা পাঠ।"
        result = detect_document_language(text)
        assert result['language'] == 'Bengali'
        assert result['confidence'] > 0.5

    def test_telugu_text(self):
        text = "హలో వరల్డ్. ఇది తెలుగు టెక్స్ట్."
        result = detect_document_language(text)
        assert result['language'] == 'Telugu'
        assert result['confidence'] > 0.5

    def test_multi_language(self):
        text = "Hello नमस्ते வணக்கம்"
        result = detect_document_language(text)
        assert result['language'] == 'Multi-language'
        assert result['confidence'] <= 0.5

    def test_empty_text(self):
        result = detect_document_language('')
        assert result['language'] == 'English'
        assert result['confidence'] == 1.0

    def test_whitespace_only(self):
        result = detect_document_language('   \n\n  \t  ')
        assert result['language'] == 'English'
        assert result['confidence'] == 1.0

    def test_numeric_only(self):
        result = detect_document_language('12345 67890 100 200')
        assert result['language'] == 'English'
        assert result['confidence'] == 1.0

    def test_mixed_numbers_and_english(self):
        text = "Invoice 12345 dated 2024-01-15 Amount $500"
        result = detect_document_language(text)
        assert result['language'] == 'English'
        assert result['confidence'] > 0.5

    def test_gujarati_text(self):
        text = "નમસ્તે દુનિયા. આ ગુજરાતી ટેક્સ્ટ છે."
        result = detect_document_language(text)
        assert result['language'] == 'Gujarati'
        assert result['confidence'] > 0.5

    def test_malayalam_text(self):
        text = "ഹലോ വേൾഡ്. ഇത് മലയാളം ടെക്സ്റ്റ് ആണ്."
        result = detect_document_language(text)
        assert result['language'] == 'Malayalam'
        assert result['confidence'] > 0.5

    def test_arabic_text(self):
        text = "مرحبا بالعالم. هذا نص عربي."
        result = detect_document_language(text)
        assert result['language'] == 'Arabic'
        assert result['confidence'] > 0.5

    def test_thai_text(self):
        text = "สวัสดีชาวโลก. นี่คือข้อความภาษาไทย."
        result = detect_document_language(text)
        assert result['language'] == 'Thai'
        assert result['confidence'] > 0.5

    def test_punjabi_text(self):
        text = "ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਦੁਨੀਆ. ਇਹ ਪੰਜਾਬੀ ਟੈਕਸਟ ਹੈ."
        result = detect_document_language(text)
        assert result['language'] == 'Punjabi'
        assert result['confidence'] > 0.5

    def test_odia_text(self):
        text = "ନମସ୍କାର ବିଶ୍ୱ. ଏହା ଓଡ଼ିଆ ପାଠ."
        result = detect_document_language(text)
        assert result['language'] == 'Odia'
        assert result['confidence'] > 0.5


class TestIsIndicText:
    def test_english_is_not_indic(self):
        assert is_indic_text("Hello world") is False

    def test_hindi_is_indic(self):
        assert is_indic_text("नमस्ते दुनिया") is True

    def test_tamil_is_indic(self):
        assert is_indic_text("வணக்கம் உலகம்") is True

    def test_empty_is_not_indic(self):
        assert is_indic_text("") is False

    def test_mixed_indic_and_english(self):
        assert is_indic_text("Hello नमस्ते world") is True

    def test_numeric_only(self):
        assert is_indic_text("12345 67890") is False

    def test_punjabi_is_indic(self):
        assert is_indic_text("ਸਤ ਸ੍ਰੀ ਅਕਾਲ") is True


class TestCountKvPatterns:
    def test_basic_kv(self):
        text = "Name: John\nAge: 30\nCity: New York"
        assert _count_kv_patterns(text) == 3

    def test_no_colon(self):
        text = "Hello world\nThis is just narrative text"
        assert _count_kv_patterns(text) == 0

    def test_empty_value(self):
        text = "Name: \nAge: 30"
        assert _count_kv_patterns(text) == 1

    def test_no_text(self):
        assert _count_kv_patterns("") == 0

    def test_long_label(self):
        text = "This is a very long label that exceeds four words: value"
        assert _count_kv_patterns(text) == 0

    def test_mixed_content(self):
        text = "Name: John\nSome narrative here\nDate: 2024-01-15\nAmount: 500"
        assert _count_kv_patterns(text) == 3


class TestCountScripts:
    def test_english_only(self):
        counts = _count_scripts("Hello World Test")
        assert counts.get('English', 0) > 0
        assert len(counts) == 1

    def test_hindi_only(self):
        counts = _count_scripts("नमस्ते दुनिया")
        assert counts.get('Hindi', 0) > 0

    def test_mixed_scripts(self):
        counts = _count_scripts("Hello नमस्ते")
        assert counts.get('English', 0) > 0
        assert counts.get('Hindi', 0) > 0

    def test_skips_digits(self):
        counts = _count_scripts("12345 67890")
        assert len(counts) == 0

    def test_skips_punctuation(self):
        counts = _count_scripts("!@#$%^&*()")
        assert len(counts) == 0

    def test_skips_whitespace(self):
        counts = _count_scripts("   \n\n  \t  ")
        assert len(counts) == 0


class TestParseJson:
    def test_plain_json(self):
        assert _parse_json('{"key": "value"}') == {"key": "value"}

    def test_json_in_code_block(self):
        result = _parse_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_empty(self):
        assert _parse_json('') is None

    def test_array(self):
        assert _parse_json('[{"label": "Name", "value": "John"}]') == [{"label": "Name", "value": "John"}]

    def test_extract_from_surrounding_text(self):
        result = _parse_json('Here is the result: {"key": "value"}')
        assert result == {"key": "value"}


class TestStripCurrency:
    def test_dollar(self):
        assert _strip_currency("$500") == "500"

    def test_euro(self):
        assert _strip_currency("€100") == "100"

    def test_rupee(self):
        assert _strip_currency("₹1000") == "1000"

    def test_no_currency(self):
        assert _strip_currency("500") == "500"

    def test_currency_with_space(self):
        assert _strip_currency("$ 500") == "500"

    def test_empty(self):
        assert _strip_currency("") == ""

    def test_pound(self):
        assert _strip_currency("£200") == "200"
