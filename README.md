Team Alpha
# 🛍️ FinSmart - Multimodal E-Commerce Search

FinSmart is an intelligent product search engine that goes beyond keywords. It allows users to search for products using *Text*, *Images*, or *Voice*, while keeping their budget in check.

## 🚀 Features
- *Multimodal Search:* Powered by AI (CLIP model), bridging text and images.
- *Voice Search:* Integrated with OpenAI Whisper for speech-to-text processing.
- *Vector Database:* Uses *Qdrant Cloud* for ultra-fast similarity search.
- *Budget Awareness:* visually indicates if a product fits the user's financial constraints.

## 🛠️ Tech Stack
- *Frontend:* Streamlit
- *Backend:* FastAPI
- *AI Models:* CLIP (ViT-B-32), Whisper (Base)
- *Database:* Qdrant (Vector DB)

## ⚙️ How to Run

1. *Clone the repository*
   ```bash
   git clone [YOUR_GITHUB_LINK_HERE]
2. **Navigate to the directory**
   ```bash
   cd FinSmart
3. Install Dependencies Make sure you have Python 3.9+ installed.

   ```bash

   pip install -r requirements.txt
   (Note: You might need to install ffmpeg locally if you are running Whisper locally)
4.Launch the Application

   ```bash

   streamlit run app.py
