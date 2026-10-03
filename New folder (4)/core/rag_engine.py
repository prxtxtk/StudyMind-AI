"""
RAG Engine — Core retrieval-augmented generation pipeline
"""

import os
import time
import streamlit as st
from typing import Optional, List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferWindowMemory


def get_available_gemini_models(api_key: str = "") -> list[str]:
    """Return verified available Gemini models for chat."""
    default_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    if not api_key:
        return default_models

    clean_key = api_key.strip()
    try:
        import urllib.request, json
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "StudyMindAI"})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                api_models = []
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    name = m.get("name", "").replace("models/", "")
                    if "generateContent" in methods and "gemini" in name.lower():
                        if not any(x in name.lower() for x in ["embed", "aqa", "imagen", "search", "vision"]):
                            api_models.append(name)
                if api_models:
                    return list(dict.fromkeys(api_models + default_models))
    except Exception:
        pass

    return default_models


class RAGEngine:
    """Central RAG engine supporting local (Ollama) and API-based LLMs."""

    def __init__(self):
        self.vectorstore: Optional[Chroma] = None
        self.llm = None
        self.embeddings = None
        self.chain = None
        self.persist_dir = "chroma_db"
        self.chat_history: List[Tuple[str, str]] = []

        # Wipe any leftover ChromaDB data from previous sessions so old
        # documents never contaminate a fresh session.
        import shutil
        if os.path.exists(self.persist_dir):
            try:
                shutil.rmtree(self.persist_dir)
            except Exception:
                pass

    # ── Embeddings ─────────────────────────────────────────────────────────────

    def get_embeddings(self):
        """Get or create local sentence-transformers embeddings (fast, consistent 384-dim)."""
        if self.embeddings is None:
            from langchain_community.embeddings import SentenceTransformerEmbeddings
            self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        return self.embeddings

    # ── Model Initialization ───────────────────────────────────────────────────

    def init_local_model(self, model_name: str = "gemma3", base_url: str = "http://localhost:11434") -> bool:
        """Initialize a local Ollama model."""
        try:
            from langchain_ollama import OllamaLLM
            self.llm = OllamaLLM(
                model=model_name,
                base_url=base_url,
                temperature=st.session_state.get("temperature", 0.3),
                num_ctx=4096,
            )
            self.get_embeddings()
            _ = self.llm.invoke("Hi")
            self._build_chain()
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ollama ({base_url}) with model '{model_name}': {e}")

    def init_openai_model(self, api_key: str, model: str = "gpt-4o-mini") -> bool:
        """Initialize an OpenAI model."""
        try:
            from langchain_openai import ChatOpenAI
            os.environ["OPENAI_API_KEY"] = api_key
            self.llm = ChatOpenAI(
                model=model,
                temperature=st.session_state.get("temperature", 0.3),
                openai_api_key=api_key,
            )
            self.get_embeddings()
            _ = self.llm.invoke("Hi")
            self._build_chain()
            return True
        except Exception as e:
            raise ValueError(f"OpenAI initialization failed: {e}")

    def init_gemini_model(self, api_key: str, model: str = "gemini-2.5-flash") -> str:
        """Initialize a Google Gemini model. Validates key via REST (no quota consumption)."""
        import urllib.request, json as _json
        from langchain_google_genai import ChatGoogleGenerativeAI

        clean_key = api_key.strip()
        os.environ["GOOGLE_API_KEY"] = clean_key

        clean_model = model.replace("models/", "").strip()
        if not clean_model or "3.8" in clean_model:
            clean_model = "gemini-2.5-flash"

        # ── Step 1: Validate key via REST (zero quota cost) ──────────────────────
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}&pageSize=1"
            req = urllib.request.Request(url, headers={"User-Agent": "StudyMindAI"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    pass  # Key is valid
                else:
                    raise ValueError("Unexpected response from Google API. Please check your key.")
        except urllib.error.HTTPError as http_err:
            body = http_err.read().decode("utf-8", errors="ignore")
            body_lower = body.lower()
            if http_err.code == 400 or "api_key_invalid" in body_lower or "api key not valid" in body_lower:
                raise ValueError("❌ Invalid Google API key. Go to https://aistudio.google.com/app/apikey to get a valid key.")
            elif http_err.code in (429, 403) or "resource_exhausted" in body_lower or "quota" in body_lower:
                raise ValueError(
                    "⚠️ Google API free-tier rate limit reached. You've used up your daily quota.\n\n"
                    "Options:\n"
                    "• Wait until midnight (Pacific Time) for the quota to reset\n"
                    "• Upgrade to a paid Google AI plan\n"
                    "• Switch to Groq (free, fast) or another provider in the sidebar"
                )
            else:
                raise ValueError(f"Google API error ({http_err.code}): {body[:300]}")
        except Exception as e:
            err_text = str(e).lower()
            if "api_key_invalid" in err_text or "api key not valid" in err_text:
                raise ValueError("❌ Invalid Google API key.")
            if "resource_exhausted" in err_text or "quota" in err_text:
                raise ValueError("⚠️ Google API daily quota exceeded. Try again tomorrow or switch providers.")
            # Network issue — warn but continue attempting to build LLM
            pass

        # ── Step 2: Build prioritized candidate list ──────────────────────────────
        candidates = [clean_model]
        for fallback in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
            if fallback not in candidates:
                candidates.append(fallback)

        last_error = None
        for candidate in candidates:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=candidate,
                    temperature=st.session_state.get("temperature", 0.3),
                    google_api_key=clean_key,
                    max_retries=1,
                    timeout=10.0,
                )
                self.get_embeddings()
                self._build_chain()
                st.session_state["gemini_model"] = candidate
                return candidate
            except Exception as e:
                last_error = e
                err_text = str(e).lower()
                if any(x in err_text for x in ["api_key_invalid", "api key not valid", "permission_denied", "unauthenticated"]):
                    raise ValueError("❌ Invalid Google API key. Please check your key in Google AI Studio.")
                if any(x in err_text for x in ["resource_exhausted", "quota"]):
                    raise ValueError(
                        "⚠️ Google API free-tier rate limit reached.\n\n"
                        "• Wait until tomorrow to reset quota\n"
                        "• Or switch to Groq (free) in the sidebar"
                    )
                continue

        raise ValueError(f"Could not initialize Gemini ({last_error}). Please verify your key in Google AI Studio.")

    def init_groq_model(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> bool:
        """Initialize a Groq model via its OpenAI-compatible API."""
        try:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=model,
                temperature=st.session_state.get("temperature", 0.3),
                openai_api_key=api_key,
                openai_api_base="https://api.groq.com/openai/v1",
                max_retries=1,
                timeout=15.0,
            )
            self.get_embeddings()
            _ = self.llm.invoke("Hi")
            self._build_chain()
            return True
        except Exception as e:
            err_text = str(e).lower()
            if "authentication" in err_text or "invalid" in err_text or "401" in err_text:
                raise ValueError("❌ Invalid Groq API key. Get one free at https://console.groq.com")
            if "rate" in err_text or "429" in err_text:
                raise ValueError("⚠️ Groq rate limit hit. Wait a moment and try again.")
            raise ValueError(f"Groq connection failed: {e}")

    def init_openrouter_model(self, api_key: str, model: str = "google/gemini-2.0-flash-exp:free") -> bool:
        """Initialize an OpenRouter model via its OpenAI-compatible API."""
        try:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=model,
                temperature=st.session_state.get("temperature", 0.3),
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://studymind-ai.app",
                    "X-Title": "StudyMind AI",
                },
                max_retries=1,
                timeout=20.0,
            )
            self.get_embeddings()
            _ = self.llm.invoke("Hi")
            self._build_chain()
            return True
        except Exception as e:
            err_text = str(e).lower()
            if "authentication" in err_text or "invalid" in err_text or "401" in err_text:
                raise ValueError("❌ Invalid OpenRouter API key. Get one at https://openrouter.ai/keys")
            if "rate" in err_text or "429" in err_text:
                raise ValueError("⚠️ OpenRouter rate limit hit. Wait a moment and try again.")
            raise ValueError(f"OpenRouter connection failed: {e}")

    # ── Vector Store ───────────────────────────────────────────────────────────

    def build_vectorstore(self, documents: List[Document], collection_name: str = "study_docs") -> None:
        """Chunk documents and upsert into ChromaDB."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=st.session_state.get("chunk_size", 1000),
            chunk_overlap=st.session_state.get("chunk_overlap", 200),
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(documents)
        emb = self.get_embeddings()

        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=emb,
                persist_directory=self.persist_dir,
                collection_name=collection_name,
            )
        else:
            self.vectorstore.add_documents(chunks)

        if hasattr(self.vectorstore, "persist"):
            try:
                self.vectorstore.persist()
            except Exception:
                pass

        self._build_chain()

    def _build_chain(self) -> None:
        """Create the conversational retrieval chain."""
        if not self.vectorstore or not self.llm:
            return

        retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": st.session_state.get("top_k", 5),
                "fetch_k": 20,
                "lambda_mult": 0.7,
            },
        )

        memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
            k=10,
        )

        qa_prompt = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template=STUDY_PROMPT_TEMPLATE,
        )

        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=False,
            combine_docs_chain_kwargs={"prompt": qa_prompt},
        )

    # ── Query ──────────────────────────────────────────────────────────────────

    def query(self, question: str, mode: str = "chat") -> dict:
        """Query the RAG pipeline."""
        if not self.chain:
            if self.llm:
                # Direct LLM call without documents
                response = self.llm.invoke(question)
                text = response.content if hasattr(response, "content") else str(response)
                return {"answer": text, "source_documents": []}
            raise RuntimeError("No AI model configured. Please connect to local Gemma 3 or an API in the sidebar.")

        prefix_map = {
            "detailed": "Please provide a very detailed, thorough explanation with step-by-step breakdown. ",
            "concise": "Please be concise, direct and brief. ",
            "eli5": "Explain this as if I were 5 years old. Use simple analogies and easy words. ",
            "chat": "",
        }
        full_q = prefix_map.get(mode, "") + question
        result = self.chain({"question": full_q, "chat_history": self.chat_history})
        self.chat_history.append((question, result["answer"]))
        return result

    def generate_quiz(self, topic: str, num_questions: int = 5, difficulty: str = "medium") -> str:
        """Generate a quiz based on indexed documents."""
        if not self.llm:
            raise RuntimeError("No AI model configured. Please connect a model in the sidebar.")

        context = ""
        if self.vectorstore:
            docs = self.vectorstore.similarity_search(topic, k=6)
            context = "\n\n".join([d.page_content for d in docs])

        prompt = QUIZ_PROMPT_TEMPLATE.format(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            context=context if context else "Use your general academic knowledge.",
        )
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def summarize(self, text: str, style: str = "structured") -> str:
        """Summarize text or topic."""
        if not self.llm:
            raise RuntimeError("No AI model configured. Please connect a model in the sidebar.")
        prompt = SUMMARY_PROMPT_TEMPLATE.format(text=text, style=style)
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def clear_history(self):
        self.chat_history = []
        if self.chain and hasattr(self.chain, "memory"):
            self.chain.memory.clear()

    def get_doc_count(self) -> int:
        if self.vectorstore:
            try:
                return self.vectorstore._collection.count()
            except Exception:
                return 0
        return 0


# ── Prompt Templates ───────────────────────────────────────────────────────────

STUDY_PROMPT_TEMPLATE = """You are StudyMind AI, an expert academic tutor and study companion. Your role is to help students understand concepts deeply, answer questions accurately using provided context, and encourage learning.

CONTEXT FROM DOCUMENTS:
{context}

CONVERSATION HISTORY:
{chat_history}

STUDENT'S QUESTION: {question}

INSTRUCTIONS:
- Answer based primarily on the provided context when available
- If the context doesn't contain enough information, clearly state this and use your general knowledge
- Structure your answer clearly with headers, bullet points, or numbered lists where appropriate
- Always cite which document/section your information comes from when possible
- Encourage deeper thinking with follow-up suggestions when relevant
- Be encouraging and supportive in tone

ANSWER:"""

QUIZ_PROMPT_TEMPLATE = """You are an expert educator creating a study quiz.

CONTEXT:
{context}

Create {num_questions} multiple-choice questions about: {topic}
Difficulty level: {difficulty}

FORMAT each question exactly like this:
**Q[number]: [Question text]**

A) [Option A]
B) [Option B]  
C) [Option C]
D) [Option D]

✅ **Correct Answer: [Letter]) [Answer text]**
💡 **Explanation:** [Brief explanation why this is correct]

---

Make questions that test deep understanding, not just memorization. Vary question types (conceptual, application, analysis)."""

SUMMARY_PROMPT_TEMPLATE = """You are an expert academic summarizer.

TEXT TO SUMMARIZE:
{text}

Create a {style} summary with:
- **Key Concepts**: Main ideas and definitions
- **Important Points**: Critical facts and relationships  
- **Examples**: Notable examples mentioned
- **Takeaways**: What a student should remember

Keep it clear, concise, and study-friendly."""
