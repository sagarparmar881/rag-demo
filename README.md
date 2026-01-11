# 🧠 RAG Demo Project

A **demo-only Retrieval-Augmented Generation (RAG)** project that shows an end-to-end flow:

1. Crawl a website and store data in **ChromaDB**
2. Run a **FastAPI backend** to query the data
3. Use a **Streamlit UI** to ask questions interactively

Simple, minimal, and easy to explain.

---

## 📁 Project Structure

```text
.
├── ingest.py        # Website crawler & ingestion (stores data in ChromaDB)
├── api.py           # FastAPI RAG backend
├── ui.py            # Streamlit UI
├── requirements.txt
└── README.md
```

---

## ⚙️ Prerequisites

- Python **3.9+**
- pip
- OpenAI API key
- ChromaDB Cloud account

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key

CHROMA_API_KEY=your_chroma_api_key
CHROMA_TENANT=your_chroma_tenant
CHROMA_DATABASE=your_chroma_database
```

---

## 📦 Dependencies

`requirements.txt`

```txt
python-dotenv>=1.0.0
crawl4ai>=0.4.0
langchain-text-splitters>=0.3.0
chromadb>=0.4.24
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
openai>=1.6.0
streamlit>=1.31.0
requests>=2.31.0
```

---

## 🛠 Installation

### Create and activate virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
```

### Upgrade pip and install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### (Optional) Verify installation

```bash
python -c "import fastapi, streamlit, chromadb, crawl4ai, openai; print('OK')"
```

---

## 🚀 How to Run (Step-by-Step)

### [1] Crawl Website → Store in ChromaDB

```bash
python ingest.py
```

- Crawls the configured website
- Splits content into chunks
- Stores embeddings in **ChromaDB**

Run once or whenever data needs refreshing.

---

### [2] Run Backend API

```bash
python api.py
```

Backend runs at:

```
http://localhost:8000
```

Health check:

```
GET /health
```

---

### [3] Run Streamlit UI

```bash
streamlit run ui.py
```

UI opens at:

```
http://localhost:8501
```

---

## 🧪 Demo Flow

1. Website content is crawled and chunked  
2. Chunks are stored in **ChromaDB**  
3. User asks a question in the UI  
4. Backend retrieves relevant chunks  
5. OpenAI generates an answer using retrieved context  

---

## 🛠 Tech Stack

- **crawl4ai** – Web crawling
- **ChromaDB (Cloud)** – Vector database
- **FastAPI** – Backend API
- **OpenAI** – LLM inference
- **Streamlit** – UI

---

## ⚠️ Notes

- Demo project only (not production-ready)
- No authentication or rate limiting
- Token counts are approximate
- Single knowledge base

---

## ❗ Common Issues

### `streamlit: command not found`
```bash
python -m streamlit run ui.py
```

### Backend not reachable
- Ensure `api.py` is running
- Check `http://localhost:8000/health`

### Missing environment variables
- Verify `.env` file exists
- Restart terminals after editing `.env`

---

## ✅ Quick Start (TL;DR)

```bash
python ingest.py
python api.py
streamlit run ui.py
```

---

Happy hacking 🤖