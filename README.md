# StudyMind-AI
## 📁 Project Structure
```
studymind-ai/
├── app.py                    # Main Streamlit app
├── requirements.txt          # Dependencies
├── .streamlit/
│   └── config.toml           # Theme config
├── core/
│   ├── rag_engine.py         # RAG pipeline (LangChain + ChromaDB)
│   └── document_processor.py # PDF/DOCX/TXT processing
├── ui/
│   ├── sidebar.py            # Model config + file upload
│   ├── chat_interface.py     # Conversational Q&A
│   ├── document_panel.py     # Document library + search
│   ├── quiz_panel.py         # Quiz generator
│   └── analytics_panel.py   # Usage analytics
├── utils/
│   └── session_state.py      # Streamlit state management
└── assets/
    └── style.css             # Custom dark theme CSS
```
## 🔧 Configuration
Adjust in the sidebar **RAG Settings**:
- **Chunk Size** — How large each indexed text chunk is (256-2048 tokens)
- **Chunk Overlap** — Overlap between chunks for context continuity
- **Top-K Retrieval** — How many chunks to retrieve per query
- **Temperature** — Response creativity (0 = factual, 1 = creative)
## 📝 Supported File Types
- `.pdf` — PDFs (all pages)
- `.txt` / `.md` — Plain text and Markdown
- `.docx` — Word documents
## 💡 Tips
- Use **Detailed** mode for complex explanations
- Use **ELI5** mode for simplified explanations of hard topics
- Use the **Quiz Generator** to self-test after studying
- Upload multiple docs for cross-document Q&A
