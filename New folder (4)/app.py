import streamlit as st
import os
import time
from pathlib import Path

st.set_page_config(
    page_title="StudyMind AI — Intelligent Study Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "StudyMind AI — Next-generation RAG-powered academic companion"
    }
)

def load_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

load_css()

from core.rag_engine import RAGEngine
from core.document_processor import DocumentProcessor
from ui.sidebar import render_sidebar
from ui.chat_interface import render_chat
from ui.document_panel import render_document_panel
from ui.quiz_panel import render_quiz
from ui.analytics_panel import render_analytics
from utils.session_state import init_session_state

init_session_state()
render_sidebar()

# 1. Hero Navbar
model_configured = st.session_state.get('model_configured', False)
provider = st.session_state.get('provider', 'Not Connected')
model_name = "Not Connected"
if provider == 'ollama':
    model_name = f"Local: {st.session_state.get('ollama_model', 'gemma3')}"
elif provider == 'openai':
    model_name = f"OpenAI: {st.session_state.get('openai_model', 'gpt-4o-mini')}"
elif provider == 'gemini':
    model_name = f"Gemini: {st.session_state.get('gemini_model', 'gemini-2.5-flash')}"
elif provider == 'groq':
    model_name = f"Groq: {st.session_state.get('groq_model', 'llama-3.3-70b-versatile')}"
elif provider == 'openrouter':
    _or_model = st.session_state.get('openrouter_model', '')
    model_name = f"OpenRouter: {_or_model.split('/')[-1] if '/' in _or_model else _or_model}"

rag_engine = st.session_state.get('rag_engine', None)
doc_count = rag_engine.get_doc_count() if hasattr(rag_engine, 'get_doc_count') else 0
chat_mode = st.session_state.get('chat_mode', 'standard')

dot_color = "#10b981" if model_configured else "#f59e0b"
dot_pulse = "pulse" if model_configured else ""

st.markdown(f"""
<div class="hero-navbar">
    <div class="brand-group">
        <div class="brand-logo-container">🧠</div>
        <div class="brand-text">
            <h2>StudyMind AI</h2>
            <span>Intelligent Academic Companion</span>
        </div>
    </div>
    <div class="hero-stats-group">
        <div class="stat-pill">
            <span class="stat-dot {dot_pulse}" style="background: {dot_color};"></span>
            {model_name}
        </div>
        <div class="stat-pill">
            📚 {doc_count} Chunks
        </div>
        <div class="stat-pill">
            ⚙️ Mode: {chat_mode.title()}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Notification Banner
if not model_configured:
    st.markdown("""
    <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 14px 20px; margin-bottom: 24px; display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 1.3rem;">✨</span>
        <div style="color: #c7d2fe; font-size: 0.9rem;"><strong style="color: #e0e7ff;">Welcome to StudyMind AI!</strong> Connect your AI model in the sidebar — choose <strong>Local Gemma 3</strong> or enter an <strong>API key</strong> to get started.</div>
    </div>
    """, unsafe_allow_html=True)

# 3. Main Content Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📁 Documents", "🧪 Quiz Lab", "📊 Analytics"])

with tab1:
    if not model_configured:
        st.markdown("""
<div class="welcome-container">
<div class="welcome-card">
<div class="welcome-hero-header">
<div class="welcome-hero-icon">🚀</div>
<h2>Ready to supercharge your learning?</h2>
<p>StudyMind AI uses advanced RAG to transform your documents into interactive knowledge — with verified citations, quizzes, and multiple cognitive modes.</p>
</div>
<div class="steps-grid">
<div class="step-card">
<div class="step-num-badge" style="background: linear-gradient(135deg, #7C3AED, #6366F1);">1</div>
<h4>Connect Your Model</h4>
<p>Use local Gemma 3 via Ollama or connect your OpenAI / Gemini API key in the sidebar.</p>
</div>
<div class="step-card">
<div class="step-num-badge" style="background: linear-gradient(135deg, #06B6D4, #0891B2);">2</div>
<h4>Upload Study Files</h4>
<p>Drop PDFs, Word docs, or notes in the Documents tab for intelligent vector indexing.</p>
</div>
<div class="step-card">
<div class="step-num-badge" style="background: linear-gradient(135deg, #10B981, #059669);">3</div>
<h4>Learn & Test</h4>
<p>Chat with verified citations, generate practice quizzes, and get structured summaries.</p>
</div>
</div>
<div class="feature-highlights-grid">
<div class="feature-highlight-card">
<div class="feature-highlight-icon" style="background: rgba(124, 58, 237, 0.15); border: 1px solid rgba(124, 58, 237, 0.25);">🎯</div>
<div>
<h5>Verified Citations</h5>
<p>Every response references the exact pages and chunks it learned from.</p>
</div>
</div>
<div class="feature-highlight-card">
<div class="feature-highlight-icon" style="background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.25);">🧪</div>
<div>
<h5>Quiz Engine</h5>
<p>Auto-generate tailored practice tests with instant grading and explanations.</p>
</div>
</div>
<div class="feature-highlight-card">
<div class="feature-highlight-icon" style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.25);">⚡</div>
<div>
<h5>4 Cognitive Modes</h5>
<p>Switch between Standard, Deep Dive, Concise bullets, and ELI5 analogies.</p>
</div>
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)
    else:
        render_chat()

with tab2:
    render_document_panel()

with tab3:
    render_quiz()

with tab4:
    render_analytics()
