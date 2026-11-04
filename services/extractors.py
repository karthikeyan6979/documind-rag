import io
import re
from collections import Counter
import pdfplumber
from docx import Document


def clean_whitespace(text):
    text = re.sub(r"[ \t]+", " ", text)      # collapse multiple spaces/tabs into one
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse 3+ newlines into just 2
    return text.strip()


def decode_text_file(content):
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for encoding in encodings_to_try:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def is_pdf_heading_line(line_text, avg_size, fontnames, body_size):
    if not line_text.strip():
        return False
    if len(line_text) > 100:
        return False
    if line_text.strip().endswith("."):
        return False
    is_bigger = avg_size > body_size + 1.5
    is_bold_font = False
    for fname in fontnames:
        if "Bold" in fname:
            is_bold_font = True
    return is_bigger or is_bold_font


#to extract text from a pdf file
def pdf_extract(file_bytes):
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() 
            if page_text:
                pages.append((i + 1, page_text))
    return pages


def pdf_extract_with_headings(file_bytes):
    all_sizes = []
    pages_data = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            words = page.extract_words(extra_attrs=["size", "fontname"])
            pages_data.append((i + 1, words))
            for w in words:
                all_sizes.append(round(w["size"]))

    if not all_sizes:
        return []

    size_counts = Counter(all_sizes)
    body_size = size_counts.most_common(1)[0][0]

    current_heading = ""
    segments = []

    for page_num, words in pages_data:
        lines = {}
        for w in words:
            key = round(w["top"])
            if key not in lines:
                lines[key] = []
            lines[key].append(w)

        sorted_tops = sorted(lines.keys())

        for top in sorted_tops:
            line_words = lines[top]
            line_words_sorted = sorted(line_words, key=lambda w: w["x0"])

            text_parts = []
            for w in line_words_sorted:
                text_parts.append(w["text"])
            line_text = " ".join(text_parts)

            total_size = 0
            for w in line_words_sorted:
                total_size += w["size"]
            avg_size = total_size / len(line_words_sorted)

            fontnames = []
            for w in line_words_sorted:
                fontnames.append(w.get("fontname", ""))

            if is_pdf_heading_line(line_text, avg_size, fontnames, body_size):
                current_heading = line_text.strip()
                continue

            if line_text.strip():
                segments.append((line_text.strip(), page_num, current_heading))

    return segments


def looks_like_heading(paragraph):
    text = paragraph.text.strip()
    if not text or len(text) > 80:
        return False
    if text.endswith("."):
        return False
    if not paragraph.runs:
        return False
    first_run = paragraph.runs[0]
    if first_run.bold:
        return True
    return False


#to extract text from a docx file
def extract_text_from_docx(file_bytes):
    stream = io.BytesIO(file_bytes)
    doc = Document(stream)
    text = ""
    #plain text extraction with heading preservation
    heading_levels = {"Heading 1": 1, "Heading 2": 2, "Heading 3": 3, "Heading 4": 4}
    current = {1: "", 2: "", 3: "", 4: ""}
    segments = []
    current_heading_flat = ""

    for paragraph in doc.paragraphs:
        para_text = paragraph.text.strip()
        if not para_text:
            continue
        style_name = paragraph.style.name

        if style_name in heading_levels:
            level = heading_levels[style_name]
            current[level] = para_text
            for i in range(level + 1, 5):
                current[i] = ""
            current_heading_flat = para_text
            continue

        if looks_like_heading(paragraph):
            current_heading_flat = para_text
            for i in range(1, 5):
                current[i] = ""
            continue

        heading_path = " > ".join(h for h in current.values() if h)
        if not heading_path:
            heading_path = current_heading_flat
        segments.append((para_text, heading_path))
        
    #text extraction from table
    for table in doc.tables:
            for row in table.rows:
                fin = []
                for cell in row.cells:
                    fin.append(cell.text)
                fin_res = "|".join(fin)
                if fin_res.strip():
                    segments.append((fin_res, "Table"))
    
    return segments
