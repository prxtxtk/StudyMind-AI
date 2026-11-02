"""
Analytics Panel — session statistics and usage insights
"""

import streamlit as st
import datetime


def render_analytics():

    st.markdown("## 📊 Study Analytics Dashboard")

    session_start = st.session_state.get("session_start")
    session_duration = (datetime.datetime.now() - session_start).seconds // 60 if session_start else 0

    messages = st.session_state.get("messages", [])
    user_messages = [m for m in messages if m["role"] == "user"]
    total_queries = len(user_messages)

    # ── Top Metrics ────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⏱️ Session Time", f"{session_duration} min")
    with col2:
        st.metric("💬 Questions Asked", total_queries)
    with col3:
        st.metric("📄 Documents", len(st.session_state.uploaded_docs) if hasattr(st.session_state, 'uploaded_docs') else 0)
    with col4:
        doc_count = st.session_state.rag_engine.get_doc_count() if hasattr(st.session_state, 'rag_engine') and st.session_state.rag_engine else 0
        st.metric("🔍 Indexed Chunks", doc_count)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        # ── Model Info ─────────────────────────────────────────────────────────
        st.markdown("### 🤖 Current Model")
        provider = st.session_state.get("provider", "not configured")
        provider_info = {
            "ollama": f"🏠 Local Ollama — {st.session_state.get('ollama_model', 'N/A')}",
            "openai": f"🔑 OpenAI — {st.session_state.get('openai_model', 'N/A')}",
            "gemini": f"✨ Google Gemini — {st.session_state.get('gemini_model', 'N/A')}",
        }
        configured = st.session_state.get("model_configured", False)

        st.markdown(f"""
        <div class="analytics-card">
            <div class="analytics-row">
                <span>Provider</span>
                <span>{provider_info.get(provider, "Not configured")}</span>
            </div>
            <div class="analytics-row">
                <span>Status</span>
                <span class="{'status-ok' if configured else 'status-err'}">
                    {'✅ Connected' if configured else '❌ Not connected'}
                </span>
            </div>
            <div class="analytics-row">
                <span>Temperature</span>
                <span>{st.session_state.get('temperature', 0.3)}</span>
            </div>
            <div class="analytics-row">
                <span>Chunk Size</span>
                <span>{st.session_state.get('chunk_size', 1000)}</span>
            </div>
            <div class="analytics-row">
                <span>Top-K Retrieval</span>
                <span>{st.session_state.get('top_k', 5)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # ── Response Mode Distribution ─────────────────────────────────────────
        st.markdown("### 💬 Response Modes Used")
        if messages:
            mode_counts = {}
            for m in messages:
                if m["role"] == "assistant":
                    mode = m.get("mode", "chat")
                    mode_counts[mode] = mode_counts.get(mode, 0) + 1

            if mode_counts:
                mode_labels = {
                    "chat": "💬 Standard",
                    "detailed": "📖 Detailed",
                    "concise": "⚡ Concise",
                    "eli5": "🐣 ELI5",
                }
                for mode, count in sorted(mode_counts.items(), key=lambda x: -x[1]):
                    pct = int(count / len([m for m in messages if m["role"] == "assistant"]) * 100)
                    st.markdown(f"""
                    <div class="mode-stat">
                        <span>{mode_labels.get(mode, mode)}</span>
                        <div class="mode-bar">
                            <div class="mode-fill" style="width:{pct}%"></div>
                        </div>
                        <span>{count} ({pct}%)</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No responses yet")
        else:
            st.info("Start asking questions to see stats!")

    st.divider()

    # ── Recent Questions ───────────────────────────────────────────────────────
    st.markdown("### 🕒 Recent Questions")
    recent = [m for m in reversed(messages) if m["role"] == "user"][:10]
    if recent:
        for i, msg in enumerate(recent):
            st.markdown(f"""
            <div class="recent-q">
                <span class="q-idx">{i+1}</span>
                <span class="q-text">{msg['content'][:120]}{"…" if len(msg['content']) > 120 else ""}</span>
                <span class="q-time">{msg.get('timestamp', '')}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No questions asked yet in this session.")

    st.divider()

    # ── Document Library Stats ─────────────────────────────────────────────────
    if hasattr(st.session_state, 'uploaded_docs') and st.session_state.uploaded_docs:
        st.markdown("### 📚 Document Library")
        for doc in st.session_state.uploaded_docs:
            file_type = doc.get("type", "txt")
            icon = {"pdf": "📕", "txt": "📄", "md": "📝", "docx": "📘"}.get(file_type, "📄")
            st.markdown(f"""
            <div class="analytics-doc">
                <span>{icon} {doc['name']}</span>
                <span>{doc.get('pages', 'N/A')} pages • {doc.get('chunks', 'N/A')} chunks</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Tips ───────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 💡 Study Tips")
    tips = [
        "📖 Upload multiple documents to enable cross-document Q&A",
        "🎯 Use **Detailed** mode for complex topics that need in-depth explanation",
        "⚡ Use **Concise** mode for quick fact checks",
        "🧪 Take a quiz after studying to reinforce your memory",
        "🔍 Use Semantic Search in the Documents tab to find specific passages",
        "📝 Export your chat history to review key insights later",
        "🔄 Adjust the Top-K retrieval slider for more or fewer source references",
    ]
    for tip in tips:
        st.markdown(f"- {tip}")
