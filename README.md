# Smart Librarian Chatbot

A FastAPI + React app that recommends books using RAG (ChromaDB with OpenAI embeddings) and then completes the answer with a tool call (`get_summary_by_title`) to show the full summary. Includes an inappropriate-language filter that blocks requests before they reach the LLM.


<img width="1917" height="1012" alt="Screenshot 2025-09-01 171457" src="https://github.com/user-attachments/assets/8d908adf-2754-4383-866f-d9a7b70ca764" />
<img width="1917" height="1009" alt="Screenshot 2025-09-01 171552" src="https://github.com/user-attachments/assets/b5948df8-2375-4f45-9243-d013d0a6dc49" />
<img width="1919" height="1017" alt="Screenshot 2025-09-01 171634" src="https://github.com/user-attachments/assets/c0939a14-8e01-4a45-ae66-79132e347cfe" />



## Features

* RAG with ChromaDB (local persistent store) + OpenAI `text-embedding-3-small`
* Conversational GPT recommendations
* Tool: `get_summary_by_title(title)` returns the full selected summary
* Offensive language filter (pre-LLM short-circuit)
* 100+ curated summaries in `data/book_summaries.txt`
* FastAPI backend, React frontend

## Run the backend

**Prerequisites:** Python 3.10+, an OpenAI API key.

```bash
# from the repo root
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt

# configure secrets (do not commit .env)
copy .env.example .env   # or: cp .env.example .env
# edit .env and set OPENAI_API_KEY=...

# start API (initializes ChromaDB and loads summaries)
python run_server.py
```

API defaults:

* Base: `http://localhost:8000`
* Health: `GET /health`
* Books list: `GET /books`
* Chat: `POST /chat`

> To reset the local vector store, stop the server and delete `backend/chroma_db/`.

## Run the frontend

**Prerequisites:** Node 18+ and npm.

```bash
cd frontend-react
npm install
npm start
```

Open `http://localhost:3000` and ask things like:

* “I want a book about freedom and social control.”
* “What do you recommend if I love fantasy stories?”
* “What is 1984?”

