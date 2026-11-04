def chunking(text, chunk_size = 500, overlap_sentence = 1):
    sentences = text.split(".")
    current_chunk = []
    current_length = 0
    chunks = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) + current_length > chunk_size and current_chunk:
            chunks.append(".".join(current_chunk) + ".")
            current_chunk = current_chunk[-overlap_sentence:]
            current_length = 0 
            for i in current_chunk:
                current_length += len(i)
        current_chunk.append(sentence)
        current_length += len(sentence)
    if current_chunk:
        chunks.append(".".join(current_chunk) + ".")

    return chunks


def chunking_with_headings(segments, chunk_size=500, overlap_sentence=1):
    grouped = []
    for text, heading in segments:
        if grouped and grouped[-1][0] == heading:
            grouped[-1][1].append(text)
        else:
            grouped.append((heading, [text]))

    result = []
    for heading, texts in grouped:
        combined = " ".join(texts)
        for c in chunking(combined, chunk_size, overlap_sentence):
            result.append((c, heading))
    return result


def chunking_pdf_with_headings(segments, chunk_size=500, overlap_sentence=1):
    grouped = []
    for text, page_num, heading in segments:
        key = (page_num, heading)
        if grouped and grouped[-1][0] == key:
            grouped[-1][1].append(text)
        else:
            grouped.append((key, [text]))

    result = []
    for key, texts in grouped:
        page_num, heading = key
        combined = " ".join(texts)
        for c in chunking(combined, chunk_size, overlap_sentence):
            result.append((c, page_num, heading))
    return result
