import os
from typing import List, Optional
from pypdf import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import streamlit as st

class RAGEngine:
    def __init__(self):
        # Using a small, efficient model for local embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def extract_text(self, uploaded_file) -> str:
        """Extract text from PDF, DOCX, or TXT."""
        extension = uploaded_file.name.split('.')[-1].lower()
        text = ""
        
        if extension == 'pdf':
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif extension == 'docx':
            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif extension == 'txt':
            text = uploaded_file.read().decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {extension}")
            
        return text

    def process_file(self, uploaded_file, session_data: dict):
        """Process an uploaded file and update the session's vector store."""
        try:
            text = self.extract_text(uploaded_file)
            if not text.strip():
                return None, "The file seems to be empty or unreadable."

            chunks = self.text_splitter.split_text(text)
            
            current_vs = session_data.get("vector_store")
            if current_vs is None:
                session_data["vector_store"] = FAISS.from_texts(chunks, self.embeddings)
            else:
                new_vs = FAISS.from_texts(chunks, self.embeddings)
                current_vs.merge_from(new_vs)
                session_data["vector_store"] = current_vs
                
            return session_data["vector_store"], f"Successfully processed {uploaded_file.name}"
        except Exception as e:
            return None, f"Error processing file: {str(e)}"

    def query_docs(self, query: str, vector_store, k: int = 3) -> str:
        """Search the provided vector store for relevant context."""
        if vector_store is None:
            return ""
        
        docs = vector_store.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in docs])
        return context

