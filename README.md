# Local RAG Document Q&A

A fully local, privacy-preserving Retrieval-Augmented Generation (RAG) system. Upload your documents, ask questions in plain language, and get streamed answers with citations pointing back to the exact source passages. No data ever leaves your machine: embeddings and generation both run locally through Ollama.

Built during an industrial AI/ML internship, with on-premise and offline deployment as the core design constraint.


## Why this exists

Most RAG tutorials assume a hosted LLM API. That is a non-starter for organizations that cannot send internal documents to third-party services. This project shows a complete RAG pipeline that runs on a single machine with no external API calls.

## Features

**Ingestion**
- PDF (pdfplumber), DOCX (python-docx, including table extraction), TXT, and URLs
- Heading preservation using style detection plus heuristics (bold, short line, no trailing period), so chunks keep their section context
- Filename sanitization and SSRF protection on URL ingestion

**Retrieval and generation**
- Local embeddings with `nomic-embed-text`, stored in ChromaDB (persistent)
- Local generation with `qwen3:1.7b` via Ollama
- Streaming responses
- Query rewriting for follow-up questions, with a `needs_rewrite()` heuristic so standalone questions are left untouched
- Citation filtering via regex, so only sources actually referenced are shown
- Post-processing to strip `<think>` blocks leaked by qwen3 models
- Session-based chat history
- Tunable temperature and top-k

**Frontend**
- Dark, console-style UI in vanilla HTML/CSS/JS
- Streaming chat, expandable citation cards, drag-and-drop document sidebar, and a live parameters panel

## Tech stack

| Layer | Tool |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Vector store | ChromaDB (PersistentClient) |
| LLM runtime | Ollama |
| Generation model | qwen3:1.7b |
| Embedding model | nomic-embed-text |
| Parsing | pdfplumber, python-docx |
| Frontend | Vanilla JS, HTML, CSS |

## Getting started

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running
- Roughly 4 GB of free disk space for the models

### Setup

```bash
# 1. Clone
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 2. Pull the models
ollama pull qwen3:1.7b
ollama pull nomic-embed-text

# 3. Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` in your browser.

> Run Uvicorn **without** `--reload`. The reloader watches the project directory, including the ChromaDB folder, and triggers re-initialization of the vector store.

### Windows one-click launch

Double-click `start.bat` (rename to match your launcher) to start the server and open the app.

## Usage

1. Drag documents into the sidebar, or paste a URL.
2. Wait for ingestion to finish. The document appears in the list.
3. Ask a question. The answer streams in with citation cards underneath.
4. Adjust temperature and top-k from the parameters panel to see how answers change.

## Project structure

```
<repo-name>/
├── main.py              # FastAPI app and routes
├── ingestion/           # Parsers, chunking, heading detection
├── retrieval/           # Embedding, ChromaDB, query rewriting
├── static/              # Frontend (HTML, CSS, JS)
├── chroma_db/           # Persistent vector store (gitignored)
├── requirements.txt
└── start.bat
```

Adjust the tree above to match the actual layout.

## Known limitations

- Scanned PDFs are not supported yet (no OCR), so image-only pages produce no text.
- Chunking is heading-aware but still size-based. It does not split on semantic boundaries.
- A 1.7B parameter model is fast and light, but weaker at multi-hop reasoning than larger models.
- No quantitative evaluation of retrieval or answer quality yet.

## Roadmap

- [ ] Evaluation framework: recall@k, MRR, latency, and faithfulness metrics
- [ ] OCR for scanned PDFs
- [ ] Improved chunking (semantic / recursive splitting)
- [ ] Hybrid retrieval (BM25 + vector) and re-ranking
- [ ] Multi-user support and per-user document isolation

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

**Karthikeyan**
B.Tech CSE, SRM University Delhi-NCR
