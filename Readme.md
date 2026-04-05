# NUST Bank RAG Assistant

Quick start guide to run the project.

## Prerequisites

- Python 3.10+
- Node.js 14+
- Ollama installed with LLaMA 3.2 model

## Setup

### 1. Create Virtual Environment
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
cd bank-assistant-frontend
npm install
cd ..
```

## Running the Project

### Terminal 1: Backend
```bash
.\.venv\Scripts\python backend.py
# or: source .venv/bin/activate && python backend.py
```
Runs on: `http://localhost:8000`

### Terminal 2: LLM Service
```bash
ollama run llama3.2
```
Runs on: `http://localhost:11434`

### Terminal 3: Frontend
```bash
cd bank-assistant-frontend
npm start
```
Runs on: `http://localhost:3000`

## Access

Open browser: `http://localhost:3000`

Admin Credentials (used for ingesting data):
- Username: `admin`
- Password: `nustbank2026`

Type a banking question and get instant answers with sources.