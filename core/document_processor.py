"""
Document Processor — handles PDF, DOCX, TXT ingestion and vectorstore indexing
"""

import io
import os
from pathlib import Path
from typing import List, Optional, Tuple
import streamlit as st
from langchain_core.documents import Document


class DocumentProcessor:
    """Loads and pre-processes various document formats into LangChain Documents."""

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc"}

    @staticmethod
    def process_uploaded_file(uploaded_file) -> List[Document]:
        """Process a Streamlit UploadedFile object into Documents."""
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix not in DocumentProcessor.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {suffix}. Supported formats: PDF, DOCX, TXT, MD")

        if hasattr(uploaded_file, "getvalue"):
            content = uploaded_file.getvalue()
        else:
            content = uploaded_file.read()

        if not content:
            raise ValueError(f"The file '{uploaded_file.name}' is empty.")

        if suffix == ".pdf":
            return DocumentProcessor._process_pdf(content, uploaded_file.name)
        elif suffix in {".txt", ".md"}:
            return DocumentProcessor._process_text(content, uploaded_file.name)
        elif suffix in {".docx", ".doc"}:
            return DocumentProcessor._process_docx(content, uploaded_file.name)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    @staticmethod
    def _process_pdf(content: bytes, filename: str) -> List[Document]:
        try:
            # Try pypdf first, then PyPDF2
            reader = None
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(content))
            except ImportError:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(content))

            documents = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    documents.append(Document(
                        page_content=text,
                        metadata={
                            "source": filename,
                            "page": i + 1,
                            "total_pages": len(reader.pages),
                            "type": "pdf",
                        }
                    ))

            if not documents:
                # Scanned or non-extractable text PDF fallback
                return [Document(
                    page_content=f"[Document: {filename} - Note: This PDF appears to be scanned or contains image-only pages. Text extraction returned no readable characters.]",
                    metadata={"source": filename, "page": 1, "total_pages": len(reader.pages) if reader else 1, "type": "pdf"}
                )]
            return documents
        except Exception as e:
            raise RuntimeError(f"PDF processing error ({filename}): {e}")

    @staticmethod
    def _process_text(content: bytes, filename: str) -> List[Document]:
        try:
            # Try UTF-8 first, fallback to Latin-1
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1", errors="replace")

            if not text.strip():
                raise ValueError("File content is empty.")

            return [Document(
                page_content=text,
                metadata={"source": filename, "type": "text"}
            )]
        except Exception as e:
            raise RuntimeError(f"Text processing error ({filename}): {e}")

    @staticmethod
    def _process_docx(content: bytes, filename: str) -> List[Document]:
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(io.BytesIO(content))
            paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)

            text = "\n\n".join(paragraphs)
            if not text.strip():
                raise ValueError("No text content found in Word document.")

            return [Document(
                page_content=text,
                metadata={"source": filename, "type": "docx"}
            )]
        except Exception as e:
            raise RuntimeError(f"DOCX processing error ({filename}): {e}")

    @staticmethod
    def get_document_stats(documents: List[Document]) -> dict:
        total_chars = sum(len(d.page_content) for d in documents)
        total_words = sum(len(d.page_content.split()) for d in documents)
        sources = list({d.metadata.get("source", "unknown") for d in documents})
        return {
            "total_documents": len(documents),
            "total_characters": total_chars,
            "total_words": total_words,
            "estimated_tokens": total_chars // 4,
            "sources": sources,
        }


def ingest_files(uploaded_files, engine) -> Tuple[int, List[str]]:
    """Helper to process and index files into RAG engine."""
    if not uploaded_files:
        return 0, []

    existing_names = {d["name"] for d in st.session_state.get("uploaded_docs", [])}
    new_files = [f for f in uploaded_files if f.name not in existing_names]

    if not new_files:
        return 0, ["Files have already been indexed."]

    processor = DocumentProcessor()
    success_count = 0
    errors = []

    for file in new_files:
        try:
            docs = processor.process_uploaded_file(file)
            stats = processor.get_document_stats(docs)
            engine.build_vectorstore(docs)
            
            st.session_state.uploaded_docs.append({
                "name": file.name,
                "type": file.name.split(".")[-1].lower(),
                "pages": f"{stats['total_words']:,} words",
                "chunks": stats["total_documents"],
                "raw_words": stats["total_words"]
            })
            success_count += 1
        except Exception as e:
            errors.append(f"{file.name}: {str(e)}")

    return success_count, errors
