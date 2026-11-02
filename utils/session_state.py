"""
Session State — centralized init for all Streamlit session variables
"""

import streamlit as st
from core.rag_engine import RAGEngine


def init_session_state():
    """Initialize all session state variables with defaults."""
    defaults = {
        # Model config
        "model_configured": False,
        "provider": "ollama",          # ollama | openai | gemini | groq | openrouter
        "ollama_model": "gemma3",
        "ollama_url": "http://localhost:11434",
        "openai_model": "gpt-4o-mini",
        "gemini_model": "gemini-2.5-flash",
        "groq_model": "llama-3.3-70b-versatile",
        "openrouter_model": "google/gemini-2.0-flash-exp:free",
        "api_key": "",
        "groq_api_key": "",
        "openrouter_api_key": "",
        "temperature": 0.3,

        # RAG settings
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "top_k": 5,

        # Documents
        "uploaded_docs": [],           # list of {name, pages, words, type}
        "processing": False,

        # Chat
        "messages": [],                # list of {role, content, sources, mode, timestamp}
        "chat_mode": "chat",           # chat | detailed | concise | eli5

        # Quiz
        "current_quiz": None,
        "quiz_answers": {},
        "quiz_submitted": False,
        "quiz_score": None,

        # Analytics
        "total_queries": 0,
        "session_start": None,

        # Engine
        "rag_engine": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Lazy-init RAG engine
    if st.session_state["rag_engine"] is None:
        st.session_state["rag_engine"] = RAGEngine()

    if st.session_state["session_start"] is None:
        import datetime
        st.session_state["session_start"] = datetime.datetime.now()
