import os
from typing import List
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

    def process_file(self, uploaded_file):
        """Process an uploaded file and create/update vector store in session state and disk."""
        try:
            text = self.extract_text(uploaded_file)
            if not text.strip():
                return False, "The file seems to be empty or unreadable."

            chunks = self.text_splitter.split_text(text)
            
            if "vector_store" not in st.session_state or st.session_state.vector_store is None:
                st.session_state.vector_store = FAISS.from_texts(chunks, self.embeddings)
            else:
                new_vs = FAISS.from_texts(chunks, self.embeddings)
                st.session_state.vector_store.merge_from(new_vs)
            
            # SAVE TO DISK: This creates a physical folder you can see
            st.session_state.vector_store.save_local("faiss_index")
                
            return True, f"Successfully processed {uploaded_file.name}"
        except Exception as e:
            return False, f"Error processing file: {str(e)}"

    def query_docs(self, query: str, k: int = 3) -> str:
        """Search the vector database for relevant context."""
        if "vector_store" not in st.session_state or st.session_state.vector_store is None:
            return ""
        
        docs = st.session_state.vector_store.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in docs])
        return context
