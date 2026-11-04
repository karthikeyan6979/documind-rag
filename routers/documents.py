import time
import uuid
import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, UploadFile, HTTPException
from config import MAX_FILE_SIZE
from state import collection
from models import DeleteRequest, URLingest
from services.ollama import get_embeddings_batch
from services.chunking import chunking, chunking_with_headings, chunking_pdf_with_headings
from services.extractors import (
    clean_whitespace,
    decode_text_file,
    pdf_extract,
    pdf_extract_with_headings,
    extract_text_from_docx,
)
from services.security import validate_url

router = APIRouter()


@router.get("/documents")
def list_documents():
    metadatas = collection.get()["metadatas"]
    filenames = list({m["filename"] for m in metadatas if m})

    return {"documents": filenames}


@router.post("/upload")
async def upload(file: UploadFile):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum allowed size is 10MB.")
    page_chunks = []
    if file.filename.endswith(".pdf"):
        segments = pdf_extract_with_headings(content)
        cleaned = []
        for t, p, h in segments:
            cleaned.append((clean_whitespace(t), p, h))
        for c, p, h in chunking_pdf_with_headings(cleaned):
            page_chunks.append((c, p, h))
        
    elif file.filename.endswith(".txt"):
        text = decode_text_file(content)
        text = clean_whitespace(text)
        chunks = chunking(text)
        for c in chunks:
            page_chunks.append((c,None, None))
        
    elif file.filename.endswith(".docx"):
        segments = extract_text_from_docx(content)
        cleaned = []
        for t, h in segments:
            cleaned.append((clean_whitespace(t), h))
        for c, h in chunking_with_headings(cleaned):
            page_chunks.append((c, None, h))

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF, TXT, or DOCX file.")
    
    collection.delete(where={"filename": file.filename})

    filtered = []
    for c, p, h in page_chunks:
        if c.strip() and len(c.strip()) > 3:
            filtered.append((c, p, h))
    page_chunks = filtered

    if not page_chunks:
        raise HTTPException(status_code=400, detail="No usable content extracted from this file.")

    chunk_texts = []
    for c, p, h in page_chunks:
        chunk_texts.append(c)

    start = time.time()#remove later
    vectors = get_embeddings_batch(chunk_texts)  
    print(f"Embedded {len(chunk_texts)} chunks in {time.time() - start:.2f}s")#remove later

    metadatas = []
    for i, (chunk_text, page_num, heading) in enumerate(page_chunks):
        meta = {"filename": file.filename, "chunk_index": i}
        if page_num is not None:
            meta["page"] = page_num
        if heading:
            meta["heading"] = heading
        metadatas.append(meta)
    
    collection.add(
        ids=[str(uuid.uuid4()) for _ in page_chunks],
        embeddings=vectors,
        documents=chunk_texts,
        metadatas=metadatas
    )

    return {"filename": file.filename, "chunks_stored": len(page_chunks)}


@router.post("/delete")
def delete(q:DeleteRequest):
    collection.delete(
        where = {"filename": q.filename}
    )
    return {"Status":"Deleted", "filename": q.filename}


@router.post("/ingest-url")
def ingest_url(req: URLingest):
    validate_url(req.url)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    try:
        response = session.get(req.url, timeout = 10)
    
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")
    
    page_chunks = []
    if req.url.endswith(".pdf") or "application/pdf" in response.headers.get("Content-Type", ""):
        pages = pdf_extract(response.content)          
        for page_num, page_text in pages:
            page_text = clean_whitespace(page_text)
            chunks = chunking(page_text)
            for c in chunks:
                page_chunks.append((c, page_num))
    else:
        soup = BeautifulSoup(response.text, "lxml")
        text = soup.get_text(separator="\n")
        text = clean_whitespace(text)
        chunks = chunking(text)
        for c in chunks:
            page_chunks.append((c, None))

    page_chunks = [(c, p) for c, p in page_chunks if c.strip() and len(c.strip()) > 3]

    if not page_chunks:
        raise HTTPException(400, "No usable content after chunking.")

    filename = req.url
    collection.delete(where={"filename": filename})

    chunk_texts = [c for c, p in page_chunks]

    vectors = get_embeddings_batch(chunk_texts)
    metadatas = []
    for i, (chunk_text, page_num) in enumerate(page_chunks):
        meta = {"filename": filename, "chunk_index": i}
        if page_num is not None:
            meta["page"] = page_num
        metadatas.append(meta)

    collection.add(
        ids=[str(uuid.uuid4()) for _ in chunk_texts],
        embeddings=vectors,
        documents=chunk_texts,
        metadatas=metadatas
    )

    return {"filename": filename, "chunks_stored": len(chunk_texts)}
