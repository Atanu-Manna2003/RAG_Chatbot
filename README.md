# RAG Pipeline - Document Q&A System

A Retrieval-Augmented Generation (RAG) pipeline that allows users to upload documents and ask questions based on their content. The system uses Groq's Llama-3.3-70b-Versatile model for fast inference and ChromaDB for vector storage.

## 🌟 Features

- **Document Upload**: Support for PDF, DOCX, TXT, and MD files
- **Smart Text Processing**: Automatic chunking and embedding generation
- **AI-Powered Q&A**: Ask questions about your documents using Groq's LLM
- **Vector Search**: Semantic search using ChromaDB
- **Clean Web Interface**: Modern, responsive frontend
- **Source Attribution**: View which parts of documents were used for answers
- **Document Management**: Upload, view, and delete documents

## 🏗️ Architecture



## 📋 Prerequisites

- Python 3.8 or higher
- Groq API key (free at [Groq Console](https://console.groq.com))
- 4GB RAM minimum, 8GB recommended

### 🔧 Setup Instructions

#### 1️⃣ Clone Repository
```bash
git clone https://github.com/yourusername/rag-pipeline.git
cd rag-pipeline

#### 2️⃣ Create Virtual Environment
python -m venv venv
# Activate it
# Windows
venv\Scripts\activate
# macOS/Linux
source myenv/bin/activate

3️⃣ Install Dependencies

pip install -r requirements.txt

4️⃣ Configure Environment

# in .env file add groq api key
GROQ_API_KEY=your_groq_api_key_here

5️⃣ Initialize Database
# run it in your terminal ->python scripts/init_db.py

6️⃣ Run Application
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

✅ Open your browser → http://localhost:8000