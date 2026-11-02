"""
Document Panel — shows uploaded documents, upload dropzone, and search
"""

import streamlit as st
import time
from core.document_processor import DocumentProcessor, ingest_files
from langchain_core.documents import Document


SAMPLE_STUDY_MATERIAL = """
# Introduction to Machine Learning & Deep Learning

Machine Learning (ML) is a subset of artificial intelligence (AI) that provides systems the ability to automatically learn and improve from experience without being explicitly programmed.

## 1. Supervised Learning
Supervised learning algorithms build a mathematical model of a set of data that contains both the inputs and the desired outputs.
- Classification: predicting categorical labels (e.g., spam vs non-spam, disease diagnosis).
- Regression: predicting continuous values (e.g., house prices, temperature forecasts).
Key algorithms include Linear Regression, Logistic Regression, Decision Trees, Random Forests, and Support Vector Machines (SVM).

## 2. Unsupervised Learning
Unsupervised learning algorithms take a set of data that contains only inputs, and find structure in the data, like grouping or clustering of data points.
- Clustering: K-Means, Hierarchical Clustering, DBSCAN.
- Dimensionality Reduction: Principal Component Analysis (PCA), t-SNE.

## 3. Deep Learning and Neural Networks
Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning.
- Perceptron: the fundamental building block of neural networks.
- Activation Functions: ReLU (Rectified Linear Unit), Sigmoid, Tanh, and Softmax.
- Optimization: Gradient Descent, Stochastic Gradient Descent (SGD), Adam Optimizer.
- Convolutional Neural Networks (CNN): Primarily used for image processing and computer vision tasks.
- Recurrent Neural Networks (RNN) and Transformers: Used for sequential data, natural language processing (NLP), and time series forecasting.

## 4. Key Challenges in ML
- Overfitting: When the model learns the training data too well, including noise, and fails to generalize to unseen test data. Mitigation: Regularization (L1, L2, Dropout), cross-validation, and more training data.
- Underfitting: When the model is too simple to capture the underlying pattern of the data.
- Bias-Variance Tradeoff: High bias can cause an algorithm to miss relevant relations (underfitting), while high variance can cause an algorithm to model random noise (overfitting).
"""


def render_document_panel():

    st.markdown("## 📁 Document Library & Study Materials")

    # ── Upload Dropzone ────────────────────────────────────────────────────────
    st.markdown("### 📤 Upload New Documents")
    col_up, col_sample = st.columns([3, 1])
    
    with col_up:
        uploaded_files = st.file_uploader(
            "Upload study documents",
            type=["pdf", "txt", "md", "docx"],
            accept_multiple_files=True,
            key="doc_panel_uploader",
            help="Supported formats: PDF, Word (DOCX), Text (TXT, MD)",
            label_visibility="collapsed"
        )
    
    with col_sample:
        if st.button("💡 Load Sample Notes", use_container_width=True, help="Load ready-made study notes on Machine Learning"):
            _load_sample_material()

    if uploaded_files:
        engine = st.session_state.rag_engine
        existing = {d["name"] for d in st.session_state.uploaded_docs}
        new_files = [f for f in uploaded_files if f.name not in existing]
        
        if new_files:
            with st.spinner(f"Processing {len(new_files)} document(s)..."):
                success_count, errors = ingest_files(new_files, engine)
                if success_count > 0:
                    st.success(f"✅ Successfully processed and indexed {success_count} file(s)!")
                    time.sleep(1)
                    st.rerun()
                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")

    st.divider()

    # ── If no documents uploaded yet ───────────────────────────────────────────
    if not st.session_state.uploaded_docs:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📚</div>
            <h3>No study materials loaded yet</h3>
            <p>Drag and drop your lecture notes, textbooks, slides, or assignments above to start indexing.<br>
            You can also click <strong>'💡 Load Sample Notes'</strong> to test immediately with Machine Learning notes!</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Summary Stats ──────────────────────────────────────────────────────────
    total_words = sum(d.get("raw_words", 0) for d in st.session_state.uploaded_docs)
    doc_count = st.session_state.rag_engine.get_doc_count() if st.session_state.rag_engine else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 Documents", len(st.session_state.uploaded_docs))
    with col2:
        st.metric("📊 Indexed Chunks", doc_count)
    with col3:
        st.metric("📝 Total Words", f"{total_words:,}")
    with col4:
        st.metric("🔍 Chunk Size", f"{st.session_state.chunk_size} tokens")

    st.divider()

    # ── Document Cards ─────────────────────────────────────────────────────────
    st.markdown("### 📚 Uploaded Study Materials")

    for i, doc in enumerate(st.session_state.uploaded_docs):
        file_type = doc.get("type", "txt")
        icon = {"pdf": "📕", "txt": "📄", "md": "📝", "docx": "📘"}.get(file_type, "📄")
        type_color = {"pdf": "#e74c3c", "txt": "#2ecc71", "md": "#9b59b6", "docx": "#3498db"}.get(file_type, "#95a5a6")

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"""
            <div class="doc-card">
                <div class="doc-card-header">
                    <span class="doc-card-icon">{icon}</span>
                    <div class="doc-card-info">
                        <div class="doc-card-name">{doc['name']}</div>
                        <div class="doc-card-meta">
                            <span class="doc-type-badge" style="background:{type_color}20;color:{type_color}">
                                {file_type.upper()}
                            </span>
                            <span>{doc.get('pages', 'N/A')}</span>
                            <span>•</span>
                            <span>{doc.get('chunks', 'N/A')} source chunks</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("🗑️ Remove", key=f"del_doc_{i}", help=f"Remove {doc['name']}"):
                st.session_state.uploaded_docs.pop(i)
                st.success(f"Removed {doc['name']}")
                time.sleep(0.5)
                st.rerun()

    st.divider()

    # ── Quick Summarize ────────────────────────────────────────────────────────
    st.markdown("### 📝 Quick Document Summarizer")
    col1, col2 = st.columns([3, 1])
    with col1:
        summarize_topic = st.text_input(
            "Topic or section to summarize",
            placeholder="e.g., 'supervised learning' or leave blank to summarize all materials",
            label_visibility="collapsed"
        )
    with col2:
        style = st.selectbox("Style", ["structured", "brief", "detailed", "bullet-points"],
                              label_visibility="collapsed")

    if st.button("📝 Generate Summary", use_container_width=True, type="primary"):
        if not st.session_state.get("model_configured", False):
            st.warning("⚠️ Please connect your AI model (Local Gemma 3 or API key) in the sidebar first.")
        else:
            engine = st.session_state.rag_engine
            with st.spinner("Generating academic summary…"):
                try:
                    query_term = summarize_topic if summarize_topic else "key concepts, main ideas, and definitions"
                    if engine.vectorstore:
                        docs = engine.vectorstore.similarity_search(query_term, k=6)
                        context = "\n\n".join([d.page_content for d in docs])
                        summary = engine.summarize(context, style=style)
                    else:
                        summary = engine.summarize(query_term, style=style)

                    st.markdown("#### 📋 Summary")
                    st.markdown(summary)
                    st.download_button(
                        "💾 Save Summary as Markdown",
                        data=summary,
                        file_name=f"summary_{(summarize_topic or 'document')[:20]}.md",
                        mime="text/markdown",
                    )
                except Exception as e:
                    st.error(f"Error generating summary: {e}")

    st.divider()

    # ── Semantic Search ────────────────────────────────────────────────────────
    st.markdown("### 🔍 Semantic Vector Search")
    search_query = st.text_input(
        "Search your documents",
        placeholder="Enter any keyword, concept, or question to find matching passages…",
        label_visibility="collapsed"
    )
    if search_query and st.session_state.rag_engine.vectorstore:
        engine = st.session_state.rag_engine
        results = engine.vectorstore.similarity_search(search_query, k=5)
        if results:
            st.markdown(f"**Found {len(results)} relevant passages:**")
            for r in results:
                src = r.metadata.get("source", "Unknown")
                page = r.metadata.get("page", "")
                page_info = f" • Page {page}" if page else ""
                st.markdown(f"""
                <div class="search-result">
                    <div class="search-result-header">📄 {src}{page_info}</div>
                    <div class="search-result-text">{r.page_content[:400]}…</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No matching passages found.")


def _load_sample_material():
    engine = st.session_state.rag_engine
    doc_name = "Sample_Machine_Learning_Notes.md"
    existing = {d["name"] for d in st.session_state.uploaded_docs}
    if doc_name in existing:
        st.info("Sample notes are already loaded!")
        return

    doc = Document(
        page_content=SAMPLE_STUDY_MATERIAL,
        metadata={"source": doc_name, "type": "md"}
    )
    processor = DocumentProcessor()
    stats = processor.get_document_stats([doc])
    engine.build_vectorstore([doc])
    st.session_state.uploaded_docs.append({
        "name": doc_name,
        "type": "md",
        "pages": f"{stats['total_words']:,} words",
        "chunks": stats["total_documents"],
        "raw_words": stats["total_words"]
    })
    st.success("✅ Sample Machine Learning notes loaded and indexed!")
    time.sleep(1)
    st.rerun()
