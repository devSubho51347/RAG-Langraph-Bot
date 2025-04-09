# RAG Chatbot with LangGraph

A scalable RAG (Retrieval Augmented Generation) chatbot built with FastAPI and LangChain.

## Features
- FastAPI-based REST API
- Async operations for improved performance
- Modular architecture with clear separation of concerns
- Type-safe with Pydantic v2 models
- Comprehensive error handling
- Built-in testing support

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with required environment variables:
```
OPENAI_API_KEY=your_api_key_here
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure
```
.
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   │   ├── config.py
│   │   └── errors.py
│   ├── models/
│   ├── services/
│   └── main.py
├── tests/
├── .env
├── requirements.txt
└── README.md
```
