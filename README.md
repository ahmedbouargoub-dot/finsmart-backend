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
## QDRANT integration
-The system connects to a managed Qdrant Cloud cluster rather than a local instance. This is defined in the configuration section of both the ingestion and search scripts.
-Client Initialization: The application initializes the QdrantClient using a specific Cloud URL and API Key.
-Collection Name: Data is stored in a collection named finsmart_products.

2. Data Ingestion (The "Writer")
The file ingest_data.py handles the ETL (Extract, Transform, Load) pipeline to populate Qdrant.


-Vectorization: It reads raw CSV data and uses the custom FinsmartBrain class (powered by CLIP-ViT-B-32) to convert product names and categories into 512-dimensional vectors.

-Embedding Strategy: The text to be embedded is formatted as: "{product_name}. Category: {category}" to ensure semantic richness.

Payload Construction: Alongside the vector, the script attaches critical metadata (Payload) to each point. This payload includes the product_name, price (sanitized to a float), and image_url.


Batch Upload: To optimize performance, data is uploaded in batches of 50 using the client.upsert method.

3. Search & Retrieval (The "Reader")
The file main.py (FastAPI backend) handles the retrieval logic, enabling the "Multimodal" search capabilities.

-Query Vector Generation: Depending on the user's input type, the system generates a query vector:


Text Search: Embeds the user's text description.


Image Search: Embeds the uploaded image bytes directly.


Audio Search: Transcribes audio via Whisper, then embeds the resulting text.


Execution: The backend executes a similarity search using q_client.search.

It targets the finsmart_products collection.

It retrieves the top 5 most semantically similar results (limit=5).


Result Parsing: The system extracts the payload (specifically price and image) from the search hits to construct the JSON response for the frontend.

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
