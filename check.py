import uvicorn
import shutil
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import Optional
from qdrant_client import QdrantClient
from core.multimodal import FinsmartBrain

# --- VOS IDENTIFIANTS INTÉGRÉS ---
QDRANT_URL = "https://42cdf35b-ac5d-474a-a783-c96835d3e3cb.europe-west3-0.gcp.cloud.qdrant.io"
QDRANT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.uimBBa-5yUfQF1EQa61Ikd-03AQKK9rNQ_h5VsIQmHw"
COLLECTION_NAME = "finsmart_products"

app = FastAPI(title="Finsmart Free API")

print("⏳ Démarrage du serveur et chargement de l'IA...")
brain = FinsmartBrain()
q_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
print("✅ Serveur prêt et connecté au Cloud !")


# --- UNIVERSAL FIX FUNCTION ---
def execute_search(client, collection, vector, limit=5):
    """
    This function checks which method exists on your specific version
    of Qdrant and uses the correct one automatically.
    """
    # 1. Try the Modern Method (v1.7+)
    if hasattr(client, "search"):
        print("🔹 Using modern .search() method")
        return client.search(
            collection_name=collection,
            query_vector=vector,
            limit=limit
        )

    # 2. Try the Legacy Method (v1.0 - v1.6)
    elif hasattr(client, "search_points"):
        print("🔸 Using legacy .search_points() method")
        response = client.search_points(
            collection_name=collection,
            vector=vector,
            limit=limit,
            with_payload=True
        )
        # Handle cases where result is nested
        return response.result if hasattr(response, "result") else response

    # 3. Last Resort (Very old versions)
    else:
        raise Exception(f"Your Qdrant Client is corrupted. Methods found: {dir(client)}")


# -----------------------------

@app.post("/search_multimodal")
async def search(
        query_text: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        input_type: str = Form(...)
):
    vector = []
    detected_content = ""

    try:
        # 1. Traitement IMAGE
        if input_type == "image" and file:
            vector = brain.process_image(file.file)
            detected_content = "Analyse d'Image"

        # 2. Traitement AUDIO
        elif input_type == "audio" and file:
            temp_filename = f"temp_{file.filename}"
            with open(temp_filename, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            vector, trans_text = brain.process_audio(temp_filename)
            detected_content = f"Audio: '{trans_text}'"
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        # 3. Traitement TEXTE
        elif input_type == "text" and query_text:
            vector = brain.process_text(query_text)
            detected_content = query_text

        # 4. RECHERCHE QDRANT (USING THE FIX)
        print(f"🔎 Searching in collection: {COLLECTION_NAME}...")

        # We call our helper function here instead of calling q_client directly
        search_result = execute_search(q_client, COLLECTION_NAME, vector, limit=5)

        results = []
        for hit in search_result:
            results.append({
                "product_name": hit.payload.get("product_name", "Inconnu"),
                "price": hit.payload.get("price", 0),
                "image_url": hit.payload.get("image_url", ""),
                "score": hit.score
            })

        return {"detected_query": detected_content, "results": results}

    except Exception as e:
        print(f"❌ Erreur Serveur: {str(e)}")
        import traceback
        traceback.print_exc()  # Prints the full error to help us debug
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)