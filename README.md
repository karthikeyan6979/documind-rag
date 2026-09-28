DocuMind

A fully local, privacy-preserving RAG (Retrieval-Augmented Generation) system for asking questions over your own documents. Nothing leaves your machine: embeddings, retrieval, and generation all run locally through Ollama.

Built as an industrial-internship project with on-premise, offline deployment in mind.

Features
Multi-format ingestion: PDF (pdfplumber), DOCX (python-docx, including tables), TXT, and web URLs
Heading preservation: style detection plus heuristics (bold text, short length, no trailing period) keep section structure in chunks
Streaming responses: answers appear token by token
Query rewriting: follow-up questions are rewritten using chat history, with a needs_rewrite() heuristic so standalone questions are left untouched
Citations: answers link back to source chunks, with regex-based citation filtering
Session-based chat history
Tunable retrieval: adjustable temperature and top-k from the UI
Security basics: SSRF protection on URL ingestion and filename sanitization on uploads
Local model output cleanup: <think> blocks from qwen3 are stripped in post-processing
Tech Stack
Layer	Tool
Backend	Python, FastAPI, Uvicorn
Vector store	ChromaDB (PersistentClient)
LLM	Ollama, qwen3:1.7b
Embeddings	Ollama, nomic-embed-text
Frontend	Vanilla HTML / CSS / JS
Architecture
Upload / URL --> Parse --> Chunk (heading-aware) --> Embed --> ChromaDB
                                                                 |
Question --> Rewrite (if follow-up) --> Embed --> Top-k retrieval
                                                                 |
                              Prompt + context --> LLM --> Streamed answer + citations
Getting Started
Prerequisites
Python 3.10+
Ollama installed and running
Setup
bash
git clone https://github.com/<your-username>/documind.git
cd documind

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

ollama pull qwen3:1.7b
ollama pull nomic-embed-text
Run
bash
uvicorn main:app

Then open http://localhost:8000.

Do not run with --reload. The file watcher picks up writes inside the ChromaDB directory and re-initializes the client.

On Windows, you can also use the one-click .bat launcher included in the repo.

Usage
Drag and drop documents into the sidebar, or paste a URL
Ask questions in the chat
Expand citation cards to see the exact source chunks
Adjust temperature and top-k from the parameters panel
Tested On
Linux Mint
Windows 10/11
Roadmap
 Evaluation framework (recall@k, MRR, latency, faithfulness)
 OCR support for scanned PDFs
 Improved chunking (semantic / recursive splitting)
 Hybrid retrieval (BM25 + vectors) and reranking
 Multi-user document isolation
Known Limitations
Small local models (1.7B) can miss details on long or ambiguous questions
Scanned PDFs without a text layer are not supported yet
Retrieval quality depends heavily on chunking; tuning is ongoing
