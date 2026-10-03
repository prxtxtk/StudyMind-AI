# 🧠 StudyMind AI — Intelligent Academic Companion & RAG Study Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/LangChain-Enabled-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain" />
  <img src="https://img.shields.io/badge/VectorDB-ChromaDB-purple?style=for-the-badge" alt="ChromaDB" />
  <img src="https://img.shields.io/badge/Providers-Ollama%20%7C%20Groq%20%7C%20Gemini%20%7C%20OpenRouter%20%7C%20OpenAI-green?style=for-the-badge" alt="Multi-Provider" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License" />
</p>

---

## 🌟 Overview

**StudyMind AI** is a next-generation study companion and Retrieval-Augmented Generation (RAG) assistant designed for students, researchers, and lifelong learners.

Upload your course notes, textbooks, lecture slides, or research papers in PDF, DOCX, or Markdown formats, and interact with your material through intelligent semantic search, verified citations, automatic practice quiz generation, smart summaries, and multi-modal cognitive responses.

StudyMind AI works seamlessly with **local offline models (Ollama Gemma 3)** or **cloud providers (Groq, Google Gemini, OpenRouter, and OpenAI)**.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🏠 **100% Offline with Ollama** | Run locally with Google Gemma 3, Llama, or any Ollama model with zero data leaving your machine. |
| 🔥 **Ultra-Fast Cloud Inference** | Native support for **Groq** (Llama 3.3 70B) for lightning-fast answers on a generous free tier. |
| 🌐 **200+ Cloud Models** | Support for **OpenRouter** (DeepSeek R1, Claude 3.5, Gemini 2.0 Flash) and **OpenAI** (GPT-4o, GPT-4o-mini). |
| ✨ **Google Gemini Integration** | Seamless connectivity to Gemini 2.5 Flash, 2.0 Flash, and Pro models via Google AI Studio. |
| 📚 **Multi-Format Document Ingestion** | Ingest PDFs, Word documents (`.docx`), Markdown (`.md`), and raw text files (`.txt`). |
| 🔍 **Maximal Marginal Relevance (MMR)** | High-precision vector retrieval powered by `sentence-transformers` (`all-MiniLM-L6-v2`) and ChromaDB to avoid redundant context. |
| 🎯 **Verified Page Citations** | Every answer explicitly references the document name and exact page numbers used. |
| 🧠 **4 Cognitive Learning Modes** | Adapt answers to your learning style: **Standard Chat**, **Detailed Breakdown**, **Concise Keypoints**, and **ELI5 Analogies**. |
| 🧪 **Interactive Quiz Lab** | Automatically generate custom multiple-choice quizzes from your uploaded documents with instant grading and explanations. |
| 📊 **Session Analytics** | Monitor chunk count, documents indexed, queries asked, and real-time engine status. |
| 🛡️ **Session Isolation** | Automatic vector database cleanup on restart ensures zero cross-session document contamination. |

---

## 🏗️ Architecture & Pipeline

```mermaid
flowchart TD
    subgraph Ingestion ["1. Document Ingestion"]
        A[Upload PDF / DOCX / TXT] --> B[Text Extraction]
        B --> C[Recursive Character Splitter<br/>Chunk Size: 1000, Overlap: 200]
        C --> D[SentenceTransformers<br/>all-MiniLM-L6-v2 Embeddings]
        D --> E[(ChromaDB Vector Store)]
    end

    subgraph Retrieval ["2. Retrieval & RAG Chain"]
        F[User Question] --> G[MMR Retriever<br/>k=5, fetch_k=20, lambda=0.7]
        E --> G
        G --> H[Conversational Retrieval Chain]
        I[Conversation Memory] --> H
    end

    subgraph Generation ["3. Model Generation"]
        H --> J{Selected Provider}
        J -->|Local| K[Ollama: Gemma 3]
        J -->|Free Fast API| L[Groq: Llama 3.3 70B]
        J -->|Google| M[Gemini 2.5 / 2.0 Flash]
        J -->|Aggregator| N[OpenRouter: 200+ Models]
        J -->|OpenAI| O[GPT-4o / GPT-4o-mini]
        K & L & M & N & O --> P[Formatted Response + Citations + Quizzes]
    end
