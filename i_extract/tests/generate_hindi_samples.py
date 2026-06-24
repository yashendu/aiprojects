"""Generate Hindi test PDF and JPEG samples for Surya OCR testing."""
import os
import io
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
SAMPLES = os.path.join(HERE, 'hindi_samples')
FONT_PATH = '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf'

SAMPLE_DOCS = [
    {
        'name': 'invoice',
        'label': 'बीजक (Invoice)',
        'fields': {
            'बीजक संख्या': 'INV-2024-001',
            'दिनांक': '15 जनवरी 2024',
            'विक्रेता का नाम': 'रमेश इलेक्ट्रॉनिक्स',
            'खरीदार का नाम': 'सुरेश ट्रेडिंग कंपनी',
            'कुल राशि': '₹ १५,४५०',
            'वस्तु': 'एलईडी टीवी ३२ इंच',
        }
    },
    {
        'name': 'identity',
        'label': 'पहचान पत्र (Identity Card)',
        'fields': {
            'नाम': 'प्रिया शर्मा',
            'पिता का नाम': 'राजेश शर्मा',
            'पता': '४२, सेक्टर १२, नोएडा, उत्तर प्रदेश',
            'जन्म तिथि': '१२ मार्च १९९२',
            'पहचान संख्या': 'ID-९८७६५४३२१',
            'रक्त समूह': 'B+',
        }
    },
    {
        'name': 'form',
        'label': 'आवेदन पत्र (Application Form)',
        'fields': {
            'आवेदक का नाम': 'अमित कुमार',
            'पिता का नाम': 'दिनेश कुमार',
            'जन्म तिथि': '२३ अगस्त १९९५',
            'मोबाइल नंबर': '९८७६५४३२१०',
            'ईमेल': 'amit.kumar@email.com',
            'पद': 'सॉफ्टवेयर डेवलपर',
        }
    },
    {
        'name': 'receipt',
        'label': 'रसीद (Receipt)',
        'fields': {
            'रसीद संख्या': 'RCP-२५६',
            'दिनांक': '०५ फरवरी २०२४',
            'प्राप्तकर्ता': 'मीरा देवी',
            'राशि': '₹ २,५००',
            'भुगतान विधि': 'नकद',
            'कारण': 'मासिक किराया',
        }
    },
    {
        'name': 'contract',
        'label': 'अनुबंध (Contract)',
        'fields': {
            'अनुबंध संख्या': 'CT-००४२',
            'दिनांक': '२० दिसंबर २०२३',
            'प्रथम पक्ष': 'विकास कंस्ट्रक्शन प्रा. लि.',
            'द्वितीय पक्ष': 'अनुराग इंफ्रास्ट्रक्चर',
            'परियोजना': 'आवासीय परिसर निर्माण',
            'अनुबंध राशि': '₹ ५,००,०००',
        }
    },
]


def get_hindi_lines():
    for doc in SAMPLE_DOCS:
        lines = [f'=== {doc["label"]} ===']
        for k, v in doc['fields'].items():
            lines.append(f'{k}: {v}')
        yield doc['name'], '\n'.join(lines), doc['fields']


def generate_hindi_jpeg(name, text, out_dir):
    img = Image.new('RGB', (600, 400), 'white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 22)
    font_bold = ImageFont.truetype(FONT_BOLD, 26)
    y = 15
    draw.text((20, y), f'{name.upper()}.jpg', fill='#333', font=font_bold)
    y += 35
    for line in text.split('\n'):
        if line.startswith('==='):
            draw.text((20, y), line.replace('=', '').strip(), fill='#7c3aed', font=font_bold)
            y += 35
        elif ': ' in line:
            parts = line.split(': ', 1)
            draw.text((20, y), parts[0] + ':', fill='#1a1a2e', font=font_bold)
            draw.text((240, y), parts[1], fill='#555', font=font)
            y += 30
        else:
            draw.text((20, y), line, fill='#333', font=font)
            y += 25
    path = os.path.join(out_dir, f'{name}.jpg')
    img.save(path, 'JPEG', quality=92)
    return path


def generate_hindi_pdf(name, text, out_dir):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_font('Noto', '', FONT_PATH, uni=True)
    pdf.add_font('Noto', 'B', FONT_BOLD, uni=True)
    pdf.add_page()
    pdf.set_font('Noto', 'B', 16)
    pdf.set_text_color(124, 58, 237)
    title = name.replace('_', ' ').title()
    pdf.cell(0, 12, f'{title} - Hindi', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Noto', '', 12)
    pdf.set_text_color(0, 0, 0)
    for line in text.split('\n'):
        if line.startswith('==='):
            pdf.set_font('Noto', 'B', 13)
            pdf.set_text_color(124, 58, 237)
            pdf.cell(0, 10, line.replace('=', '').strip(), new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('Noto', '', 12)
            pdf.set_text_color(0, 0, 0)
        elif ': ' in line:
            parts = line.split(': ', 1)
            pdf.set_font('Noto', 'B', 12)
            pdf.cell(60, 8, parts[0] + ':')
            pdf.set_font('Noto', '', 12)
            pdf.cell(0, 8, parts[1], new_x='LMARGIN', new_y='NEXT')
        else:
            pdf.cell(0, 8, line, new_x='LMARGIN', new_y='NEXT')
    path = os.path.join(out_dir, f'{name}.pdf')
    pdf.output(path)
    return path


def main():
    os.makedirs(SAMPLES, exist_ok=True)
    print(f'Generating Hindi test samples in {SAMPLES}/')
    for name, text, fields in get_hindi_lines():
        jpg_path = generate_hindi_jpeg(name, text, SAMPLES)
        pdf_path = generate_hindi_pdf(name, text, SAMPLES)
        print(f'  {name}:')
        print(f'    JPEG: {jpg_path}')
        print(f'    PDF:  {pdf_path}')
    print(f'\nGenerated {len(SAMPLE_DOCS)} Hindi samples (PDF + JPEG each)')


if __name__ == '__main__':
    main()
