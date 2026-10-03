"""
Sidebar UI — model configuration, document upload, settings
"""

import streamlit as st
import time
from core.document_processor import DocumentProcessor, ingest_files


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)

        # ── Logo / Branding ─────────────────────────────────────────────────────
        st.markdown("""
        <div class="sidebar-logo" style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
            <span style="font-size: 1.5em;">🧠</span> 
            <strong style="background: linear-gradient(90deg, #4F46E5, #9333EA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.2em;">StudyMind AI</strong>
            <span style="background: rgba(99, 102, 241, 0.1); color: #4F46E5; padding: 2px 6px; border-radius: 4px; font-size: 0.7em; font-weight: bold;">v2.0</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Model Connection Status Badge ───────────────────────────────────────
        if st.session_state.get("model_configured", False):
            provider_label = {
                "ollama": f"Local: {st.session_state.get('ollama_model', 'gemma3')}",
                "openai": f"OpenAI: {st.session_state.get('openai_model', 'gpt-4o-mini')}",
                "gemini": f"Gemini: {st.session_state.get('gemini_model', 'gemini-2.5-flash')}",
                "groq": f"Groq: {st.session_state.get('groq_model', 'llama-3.3-70b-versatile')}",
                "openrouter": f"OpenRouter: {st.session_state.get('openrouter_model', 'gemini-2.0-flash')}",
            }.get(st.session_state.provider, "Connected")
            st.markdown(f"""
            <div class="status-card-connected" style="margin-bottom: 14px; border-left: 4px solid #10B981; padding: 10px; background: rgba(16, 185, 129, 0.1); color: #10B981; border-radius: 4px; display: flex; align-items: center; gap: 8px;">
                <span class="stat-dot online" style="height: 8px; width: 8px; background-color: #10B981; border-radius: 50%; display: inline-block;"></span>
                <span>Ready: <strong>{provider_label}</strong></span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card-standby" style="margin-bottom: 14px; border-left: 4px solid #F59E0B; padding: 10px; background: rgba(245, 158, 11, 0.1); color: #F59E0B; border-radius: 4px; display: flex; align-items: center; gap: 8px;">
                <span class="stat-dot standby" style="height: 8px; width: 8px; background-color: #F59E0B; border-radius: 50%; display: inline-block;"></span>
                <span>Status: <strong>No Model Connected</strong></span>
            </div>
            """, unsafe_allow_html=True)

        # ── Model Configuration ─────────────────────────────────────────────────
        st.markdown('<div class="sidebar-category-header" style="font-weight: 600; text-transform: uppercase; font-size: 0.8em; color: #6B7280; margin-top: 20px; margin-bottom: 10px;">AI Provider</div>', unsafe_allow_html=True)

        _PROVIDER_OPTIONS = [
            "🏠 Local (Ollama)",
            "🔑 OpenAI",
            "✨ Google Gemini",
            "🔥 Groq (Free)",
            "🌐 OpenRouter",
        ]
        _PROVIDER_MAP = {
            "🏠 Local (Ollama)": "ollama",
            "🔑 OpenAI": "openai",
            "✨ Google Gemini": "gemini",
            "🔥 Groq (Free)": "groq",
            "🌐 OpenRouter": "openrouter",
        }
        _PROVIDER_REVERSE = {v: k for k, v in _PROVIDER_MAP.items()}

        provider = st.radio(
            "Choose provider",
            options=_PROVIDER_OPTIONS,
            index=_PROVIDER_OPTIONS.index(
                _PROVIDER_REVERSE.get(st.session_state.provider, "🏠 Local (Ollama)")
            ),
            label_visibility="collapsed",
        )

        st.session_state.provider = _PROVIDER_MAP[provider]

        # ── Provider-specific fields ────────────────────────────────────────────
        if st.session_state.provider == "ollama":
            _render_ollama_config()
        elif st.session_state.provider == "openai":
            _render_openai_config()
        elif st.session_state.provider == "gemini":
            _render_gemini_config()
        elif st.session_state.provider == "groq":
            _render_groq_config()
        elif st.session_state.provider == "openrouter":
            _render_openrouter_config()

        st.divider()

        # ── Document Upload (ALWAYS ACCESSIBLE) ──────────────────────────────────
        st.markdown('<div class="sidebar-category-header" style="font-weight: 600; text-transform: uppercase; font-size: 0.8em; color: #6B7280; margin-top: 20px; margin-bottom: 10px;">Knowledge Base Upload</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload study files (PDF, DOCX, TXT, MD)",
            type=["pdf", "txt", "md", "docx"],
            accept_multiple_files=True,
            key="sidebar_doc_uploader",
            help="Files are processed and indexed with fast local embeddings"
        )
        if uploaded:
            _handle_sidebar_uploads(uploaded)

        # Document counter badge
        doc_count = st.session_state.rag_engine.get_doc_count() if st.session_state.get("rag_engine") else 0
        if doc_count > 0:
            st.markdown(f"""
            <div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 8px; padding: 8px 12px; font-size: 0.82rem; color: #A5B4FC; text-align: center; margin: 10px 0;">
                📚 <strong>{doc_count}</strong> Chunks indexed in Vector DB
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.uploaded_docs:
            for doc in st.session_state.uploaded_docs:
                st.markdown(f"""
                <div class="doc-item" style="display: flex; align-items: center; padding: 6px 8px; background: #1F2937; border-radius: 6px; margin-bottom: 6px; font-size: 0.85em;">
                    <span class="doc-icon" style="margin-right: 8px;">{_file_icon(doc['type'])}</span>
                    <span class="doc-name" style="flex-grow: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{doc['name']}</span>
                    <span class="doc-meta" style="color: #9CA3AF; font-size: 0.9em;">{doc.get('pages', '')}</span>
                </div>
                """, unsafe_allow_html=True)

        # ── RAG Settings ────────────────────────────────────────────────────────
        with st.expander("⚙️ Retrieval Parameters", expanded=False):
            st.session_state.chunk_size = st.slider(
                "Chunk Size", 256, 2048, st.session_state.chunk_size, 64,
                help="Size of text chunks for indexing"
            )
            st.session_state.chunk_overlap = st.slider(
                "Chunk Overlap", 0, 512, st.session_state.chunk_overlap, 32,
                help="Overlap between consecutive chunks"
            )
            st.session_state.top_k = st.slider(
                "Retrieved Chunks (k)", 1, 10, st.session_state.top_k, 1,
                help="Number of relevant chunks to retrieve per query"
            )
            st.session_state.temperature = st.slider(
                "Temperature", 0.0, 1.0, st.session_state.temperature, 0.05,
                help="Higher = more creative, Lower = factual"
            )

        # ── Chat Mode ───────────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-category-header" style="font-weight: 600; text-transform: uppercase; font-size: 0.8em; color: #6B7280; margin-top: 20px; margin-bottom: 10px;">Cognitive Style</div>', unsafe_allow_html=True)
        mode_options = {
            "💬 Standard": "chat",
            "📖 Detailed Breakdown": "detailed",
            "⚡ Concise Keypoints": "concise",
            "🐣 ELI5 Analogies": "eli5",
        }
        selected_mode = st.selectbox(
            "Mode",
            list(mode_options.keys()),
            index=list(mode_options.values()).index(st.session_state.chat_mode),
            label_visibility="collapsed",
        )
        st.session_state.chat_mode = mode_options[selected_mode]

        # ── Actions ─────────────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-category-header" style="font-weight: 600; text-transform: uppercase; font-size: 0.8em; color: #6B7280; margin-top: 20px; margin-bottom: 10px;">Session Controls</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                if st.session_state.rag_engine:
                    st.session_state.rag_engine.clear_history()
                st.rerun()
        with col2:
            if st.button("♻️ Reset All", use_container_width=True):
                _full_reset()

        st.markdown('</div>', unsafe_allow_html=True)


# ── Sub-renderers ──────────────────────────────────────────────────────────────

def _render_ollama_config():
    st.session_state.ollama_url = st.text_input(
        "Ollama URL", st.session_state.ollama_url,
        help="Default: http://localhost:11434"
    )
    
    # Try fetching installed models from Ollama dynamically
    installed_models = []
    try:
        import urllib.request, json
        req = urllib.request.Request(f"{st.session_state.ollama_url}/api/tags", headers={"User-Agent": "StudyMind"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            installed_models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        pass

    default_models = ["gemma3:latest", "gemma3", "gemma3:4b", "gemma3:12b", "gemma2", "llama3.2"]
    # Put installed models first
    all_models = list(dict.fromkeys(installed_models + default_models))
    current = st.session_state.ollama_model
    if current not in all_models:
        all_models.insert(0, current)

    idx = 0
    if current in all_models:
        idx = all_models.index(current)
    elif installed_models:
        idx = 0

    st.session_state.ollama_model = st.selectbox("Model", all_models, index=idx)

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🔌 Connect Ollama", use_container_width=True, type="primary"):
            _connect_ollama()
    with col2:
        if st.button("🔍 Check", use_container_width=True, help="Test if Ollama server is running"):
            _check_ollama_status()


def _render_openai_config():
    st.session_state.api_key = st.text_input(
        "OpenAI API Key", st.session_state.api_key,
        type="password", placeholder="sk-..."
    )
    models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    st.session_state.openai_model = st.selectbox("Model", models)

    if st.button("🔑 Connect to OpenAI", use_container_width=True, type="primary"):
        _connect_openai()


def _render_gemini_config():
    st.session_state.api_key = st.text_input(
        "Google API Key", st.session_state.api_key,
        type="password", placeholder="AIza..."
    )
    
    from core.rag_engine import get_available_gemini_models
    models = get_available_gemini_models(st.session_state.api_key)
    
    current = st.session_state.gemini_model
    # Clean up any previously stored invalid model names
    if not current or any(x in str(current) for x in ["3.8", "3.5", "3.7", "3.1"]):
        current = "gemini-2.5-flash"
        st.session_state.gemini_model = current

    if current not in models:
        models.insert(0, current)

    idx = models.index(current) if current in models else 0
    st.session_state.gemini_model = st.selectbox("Model", models, index=idx)

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        if st.button("✨ Connect to Gemini", use_container_width=True, type="primary"):
            _connect_gemini()
    with col_btn2:
        if st.button("🔄 Refresh", use_container_width=True, help="Query Google API for models authorized on your key"):
            st.rerun()


# ── Connection helpers ─────────────────────────────────────────────────────────

def _render_groq_config():
    st.markdown("""
    <div style="background: rgba(255,102,0,0.08); border: 1px solid rgba(255,102,0,0.25); border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; color: #FCA5A5; margin-bottom: 12px;">
        🔥 <strong>Groq</strong> — Blazing fast inference, generous free tier.<br>
        Get your free key at <a href="https://console.groq.com" target="_blank" style="color:#F97316;">console.groq.com</a>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.groq_api_key = st.text_input(
        "Groq API Key", st.session_state.groq_api_key,
        type="password", placeholder="gsk_..."
    )

    groq_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]
    current_groq = st.session_state.groq_model
    if current_groq not in groq_models:
        groq_models.insert(0, current_groq)
    st.session_state.groq_model = st.selectbox("Model", groq_models,
        index=groq_models.index(current_groq) if current_groq in groq_models else 0)

    if st.button("🔥 Connect to Groq", use_container_width=True, type="primary"):
        _connect_groq()


def _render_openrouter_config():
    st.markdown("""
    <div style="background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.25); border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; color: #93C5FD; margin-bottom: 12px;">
        🌐 <strong>OpenRouter</strong> — Access 200+ models incl. Claude, Gemini, GPT, Llama.<br>
        Get your free key at <a href="https://openrouter.ai/keys" target="_blank" style="color:#60A5FA;">openrouter.ai/keys</a>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.openrouter_api_key = st.text_input(
        "OpenRouter API Key", st.session_state.openrouter_api_key,
        type="password", placeholder="sk-or-..."
    )

    openrouter_models = [
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "microsoft/phi-4:free",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini",
        "google/gemini-2.5-pro-preview",
        "deepseek/deepseek-r1:free",
        "qwen/qwen3-235b-a22b:free",
    ]
    current_or = st.session_state.openrouter_model
    if current_or not in openrouter_models:
        openrouter_models.insert(0, current_or)
    st.session_state.openrouter_model = st.selectbox("Model", openrouter_models,
        index=openrouter_models.index(current_or) if current_or in openrouter_models else 0)

    if st.button("🌐 Connect to OpenRouter", use_container_width=True, type="primary"):
        _connect_openrouter()



def _check_ollama_status():
    import urllib.request
    try:
        req = urllib.request.Request(f"{st.session_state.ollama_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                st.success("✅ Ollama server is active and reachable!")
            else:
                st.warning(f"Ollama returned HTTP status {resp.status}")
    except Exception as e:
        st.error(f"❌ Cannot reach Ollama at {st.session_state.ollama_url}.\\n\\nTip: Start Ollama from your Start menu or run `ollama serve` in terminal.")


def _connect_ollama():
    engine = st.session_state.rag_engine
    with st.spinner(f"Connecting to Ollama ({st.session_state.ollama_model})..."):
        try:
            engine.init_local_model(
                model_name=st.session_state.ollama_model,
                base_url=st.session_state.ollama_url,
            )
            st.session_state.model_configured = True
            st.success(f"✅ Connected to {st.session_state.ollama_model}!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")
            st.info("💡 Make sure Ollama is running. Run `ollama serve` in PowerShell or open the Ollama app from Start Menu.")


def _connect_openai():
    if not st.session_state.api_key:
        st.error("Please enter your OpenAI API key")
        return
    engine = st.session_state.rag_engine
    with st.spinner("Connecting to OpenAI..."):
        try:
            engine.init_openai_model(st.session_state.api_key, st.session_state.openai_model)
            st.session_state.model_configured = True
            st.success(f"✅ Connected! {st.session_state.openai_model} ready")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"❌ {e}")


def _connect_gemini():
    if not st.session_state.api_key:
        st.error("Please enter your Google API key")
        return
    engine = st.session_state.rag_engine
    with st.spinner("Verifying API key and connecting to Gemini..."):
        try:
            connected_model = engine.init_gemini_model(st.session_state.api_key, st.session_state.gemini_model)
            st.session_state.model_configured = True
            st.session_state.gemini_model = connected_model
            st.success(f"✅ Connected to Gemini ({connected_model})!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(str(e))


def _connect_groq():
    if not st.session_state.groq_api_key:
        st.error("Please enter your Groq API key")
        return
    engine = st.session_state.rag_engine
    with st.spinner(f"Connecting to Groq ({st.session_state.groq_model})..."):
        try:
            engine.init_groq_model(st.session_state.groq_api_key, st.session_state.groq_model)
            st.session_state.model_configured = True
            st.success(f"✅ Connected to Groq ({st.session_state.groq_model})!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(str(e))


def _connect_openrouter():
    if not st.session_state.openrouter_api_key:
        st.error("Please enter your OpenRouter API key")
        return
    engine = st.session_state.rag_engine
    with st.spinner(f"Connecting to OpenRouter ({st.session_state.openrouter_model})..."):
        try:
            engine.init_openrouter_model(st.session_state.openrouter_api_key, st.session_state.openrouter_model)
            st.session_state.model_configured = True
            st.success(f"✅ Connected via OpenRouter ({st.session_state.openrouter_model})!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(str(e))




def _handle_sidebar_uploads(uploaded_files):
    engine = st.session_state.rag_engine
    existing_names = {d["name"] for d in st.session_state.uploaded_docs}
    new_files = [f for f in uploaded_files if f.name not in existing_names]
    
    if not new_files:
        return

    with st.spinner(f"Processing and indexing {len(new_files)} document(s)..."):
        success_count, errors = ingest_files(new_files, engine)
        if success_count > 0:
            st.success(f"✅ Successfully indexed {success_count} file(s)!")
            time.sleep(1)
            st.rerun()
        if errors:
            for err in errors:
                st.error(f"❌ {err}")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _file_icon(file_type: str) -> str:
    return {"pdf": "📕", "txt": "📄", "md": "📝", "docx": "📘", "doc": "📘"}.get(file_type, "📄")


def _full_reset():
    import shutil, os
    for key in ["messages", "uploaded_docs", "current_quiz", "quiz_answers",
                "quiz_submitted", "quiz_score", "model_configured", "total_queries"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.rag_engine = None
    if os.path.exists("chroma_db"):
        try:
            shutil.rmtree("chroma_db")
        except Exception:
            pass
    st.rerun()
