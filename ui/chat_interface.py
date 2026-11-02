"""
Chat Interface — conversational Q&A with source citations
"""

import streamlit as st
import datetime
import time


def render_chat():
    engine = st.session_state.rag_engine

    # ── Chat Container ──────────────────────────────────────────────────────────
    chat_container = st.container()

    with chat_container:
        if not st.session_state.messages:
            _render_empty_state()
        else:
            for msg in st.session_state.messages:
                _render_message(msg)

    # ── Input Bar ───────────────────────────────────────────────────────────────
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([7, 1, 1])
    with col1:
        user_input = st.chat_input(
            placeholder="Ask anything about your study materials… (e.g., 'Explain photosynthesis' or 'Summarize chapter 3')",
        )
    with col2:
        summarize_btn = st.button("📝 Summarize", use_container_width=True,
                                   help="Summarize the last uploaded document")
    with col3:
        export_btn = st.button("💾 Export", use_container_width=True,
                                help="Export chat history")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Suggested Questions ─────────────────────────────────────────────────────
    if not st.session_state.messages and st.session_state.uploaded_docs:
        st.markdown("**💡 Try asking:**")
        suggestions = [
            "What are the main concepts in this document?",
            "Create a summary of the key points",
            "What are the most important definitions?",
            "Explain the relationship between the main topics",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"💬 {s}", key=f"sug_{i}", use_container_width=True):
                    user_input = s

    # ── Handle Input ────────────────────────────────────────────────────────────
    if user_input:
        _handle_user_message(user_input, engine)

    if summarize_btn and st.session_state.uploaded_docs:
        _handle_user_message("Please provide a comprehensive summary of all the documents I've uploaded, covering main topics, key concepts, and important details.", engine)

    if export_btn and st.session_state.messages:
        _export_chat()


# ── Message Rendering ──────────────────────────────────────────────────────────

def _render_empty_state():
    doc_uploaded = len(st.session_state.uploaded_docs) > 0
    if doc_uploaded:
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px; background: rgba(16, 20, 30, 0.4); border: 2px dashed rgba(99, 102, 241, 0.5); border-radius: 16px; margin: 20px 0;">
            <div style="font-size: 2.8rem; margin-bottom: 12px;">🧠</div>
            <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 6px; color: #F8FAFC;">Knowledge Base Connected & Ready</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; max-width: 500px; margin: 0 auto 16px auto;">
                Your course materials are embedded and ready. Ask any question below or choose a suggested topic!
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px; background: rgba(16, 20, 30, 0.4); border: 2px dashed rgba(255, 255, 255, 0.2); border-radius: 16px; margin: 20px 0;">
            <div style="font-size: 2.8rem; margin-bottom: 12px;">📚</div>
            <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 6px; color: #F8FAFC;">No Documents Yet</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; max-width: 520px; margin: 0 auto;">
                Upload your lecture slides or notes in the <strong>Document Hub</strong> for verified source citations, or ask general academic questions right away!
            </p>
        </div>
        """, unsafe_allow_html=True)


def _render_message(msg: dict):
    role = msg["role"]
    content = msg["content"]
    sources = msg.get("sources", [])
    timestamp = msg.get("timestamp", "")
    mode = msg.get("mode", "chat")

    if role == "user":
        st.markdown(f"""
        <div class="chat-bubble-user" style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
            <div class="chat-bubble-user-inner" style="background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 12px 18px; border-radius: 18px 18px 4px 18px; max-width: 80%; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                {content}
                <div style="font-size: 0.72rem; color: rgba(255, 255, 255, 0.7); text-align: right; margin-top: 4px;">{timestamp}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        mode_badge = {
            "detailed": '<span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34D399; padding: 2px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; margin-bottom: 8px; display: inline-block;">📖 Detailed Deep Dive</span>',
            "concise": '<span style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); color: #FBBF24; padding: 2px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; margin-bottom: 8px; display: inline-block;">⚡ Concise Summary</span>',
            "eli5": '<span style="background: rgba(244, 63, 94, 0.15); border: 1px solid rgba(244, 63, 94, 0.3); color: #FB7185; padding: 2px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; margin-bottom: 8px; display: inline-block;">🐣 ELI5 Analogy</span>',
            "chat": '',
        }.get(mode, '')

        with st.chat_message("assistant", avatar="🧠"):
            if mode_badge:
                st.markdown(mode_badge, unsafe_allow_html=True)
            st.markdown(content)

            if sources:
                with st.expander(f"🔍 Verified Document Citations ({len(sources)} passage{'s' if len(sources) > 1 else ''})", expanded=False):
                    for j, src in enumerate(sources):
                        src_meta = src.metadata if hasattr(src, 'metadata') else {}
                        src_name = src_meta.get("source", f"Source {j+1}")
                        src_page = src_meta.get("page", "")
                        page_badge = f'<span style="background: rgba(99, 102, 241, 0.2); color: #A5B4FC; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-left: 8px;">Page {src_page}</span>' if src_page else ""
                        preview = src.page_content[:320] if hasattr(src, 'page_content') else str(src)[:320]
                        st.markdown(f"""
                        <div class="source-card" style="border-left: 3px solid #6366f1; background: rgba(30, 41, 59, 0.5); padding: 12px; border-radius: 0 8px 8px 0; margin-bottom: 12px;">
                            <div class="source-header" style="font-weight: 600; color: #e2e8f0; margin-bottom: 6px; display: flex; align-items: center;">
                                <span>📄 {src_name}</span>
                                {page_badge}
                            </div>
                            <div class="source-preview" style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5;">"{preview}…"</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown(f'<div style="font-size: 0.72rem; color: #64748B; margin-top: 6px;">{timestamp}</div>', unsafe_allow_html=True)


# ── Message Handler ────────────────────────────────────────────────────────────

def _handle_user_message(text: str, engine):
    timestamp = datetime.datetime.now().strftime("%H:%M")

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": text,
        "timestamp": timestamp,
    })
    st.session_state.total_queries += 1

    # Stream assistant response
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Thinking…"):
            try:
                result = engine.query(text, mode=st.session_state.chat_mode)
                answer = result.get("answer", str(result))
                sources = result.get("source_documents", [])

                st.markdown(answer)

                if sources:
                    with st.expander(f"🔍 Verified Document Citations ({len(sources)} passage{'s' if len(sources) > 1 else ''})", expanded=False):
                        for j, src in enumerate(sources):
                            src_meta = src.metadata if hasattr(src, 'metadata') else {}
                            src_name = src_meta.get("source", f"Source {j+1}")
                            src_page = src_meta.get("page", "")
                            page_badge = f'<span style="background: rgba(99, 102, 241, 0.2); color: #A5B4FC; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-left: 8px;">Page {src_page}</span>' if src_page else ""
                            preview = src.page_content[:320] if hasattr(src, 'page_content') else str(src)[:320]
                            st.markdown(f"""
                            <div class="source-card" style="border-left: 3px solid #6366f1; background: rgba(30, 41, 59, 0.5); padding: 12px; border-radius: 0 8px 8px 0; margin-bottom: 12px;">
                                <div class="source-header" style="font-weight: 600; color: #e2e8f0; margin-bottom: 6px; display: flex; align-items: center;">
                                    <span>📄 {src_name}</span>
                                    {page_badge}
                                </div>
                                <div class="source-preview" style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5;">"{preview}…"</div>
                            </div>
                            """, unsafe_allow_html=True)

                # Persist message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "mode": st.session_state.chat_mode,
                    "timestamp": datetime.datetime.now().strftime("%H:%M"),
                })

            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.datetime.now().strftime("%H:%M"),
                })

    st.rerun()


# ── Export ─────────────────────────────────────────────────────────────────────

def _export_chat():
    lines = ["# StudyMind AI — Chat Export\n"]
    for msg in st.session_state.messages:
        role = "You" if msg["role"] == "user" else "StudyMind AI"
        ts = msg.get("timestamp", "")
        lines.append(f"## {role} [{ts}]\n{msg['content']}\n")
    content = "\n---\n".join(lines)
    st.download_button(
        "⬇️ Download Chat",
        data=content,
        file_name=f"studymind_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
    )
