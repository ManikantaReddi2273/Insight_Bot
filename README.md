# 🧠 InsightBot: Enterprise-Grade AI Intelligence

InsightBot is a powerful, multi-modal AI assistant designed to provide deep insights from your documents while maintaining a real-time connection to the global web. It combines **Retrieval-Augmented Generation (RAG)**, **Live Web Research**, and **AI Image Synthesis** into a single, premium user interface.

---

## 🌟 The Core Idea
In today’s information-heavy world, users struggle with "information silos"—important data is trapped in static documents (PDFs, DOCX), while current events are only available on the web. **InsightBot bridges this gap.** 

It serves as a central intelligence hub where you can chat with your data, verify it against real-time web sources, and visualize concepts—all in one place.

---

## 🚀 Key Features

- **📂 Document Intelligence (RAG):** Upload PDFs, Word docs, or Text files. InsightBot indexes them into a local vector database (FAISS) for instant, context-aware querying.
- **🔍 Real-Time Web Search:** When documents don't have the answer, InsightBot autonomously searches the web via Serper API to provide up-to-the-minute facts.
- **🎨 Artistic Visualization:** Generate high-quality images using the **FLUX.1-schnell** model directly within the chat interface.
- **💎 Premium UI/UX:** A modern "Glassmorphism" interface built with Streamlit, featuring chat history, file chips, and smooth micro-animations.
- **💾 Session Persistence:** Automatically saves your chat history and local document indexes for continued work.

---

## 🔥 How It Helps You
1. **Accelerated Research:** Summarize hundreds of pages of documents in seconds.
2. **Fact-Checking:** Verify internal data against current web trends and news.
3. **Creative Workflow:** Brainstorm ideas and instantly generate visual mockups or concept art.
4. **Data Privacy:** Your documents are processed locally into vector embeddings, giving you enterprise-level control.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Streamlit (Python) |
| **LLM Engine** | Groq (Llama-3.1-8b-instant) |
| **Vector DB** | FAISS (Meta) |
| **Embeddings** | Hugging Face (`all-MiniLM-L6-v2`) |
| **Image Gen** | Black Forest Labs (FLUX.1-schnell via Hugging Face Hub) |
| **Web Search** | Serper API (Google Search) |
| **Document Parsing** | PyPDF, python-docx |

---

## 💻 Installation Guide

Follow these steps to set up InsightBot on your local machine:

### 1. Prerequisites
- Python 3.9 or higher installed.
- API Keys for: [Groq](https://console.groq.com/), [Serper](https://serper.dev/), and [Hugging Face](https://huggingface.co/settings/tokens).

### 2. Clone the Repository
```bash
git clone https://github.com/YourUsername/InsightBot.git
cd InsightBot
```

### 3. Create a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Environment Configuration
Create a `.env` file in the root directory and add your keys:
```env
GROQ_API_KEY=your_groq_api_key
SERPER_API_KEY=your_serper_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

### 6. Run the Application
```powershell
streamlit run main.py
```

---

## 📜 License
Internal Project - All Rights Reserved.

---
*Developed with ❤️ for Advanced AI Research.*
