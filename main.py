import uvicorn
import shutil
import os
import httpx  # We use this to talk to Qdrant directly
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
# We still keep this to check connection, but we won't use it for search
q_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
print("✅ Serveur prêt et connecté au Cloud !")


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

        # 4. RECHERCHE (DIRECT HTTP METHOD)
        # This bypasses the broken Python library and talks to the API directly.
        print(f"🔎 Searching in collection: {COLLECTION_NAME}...")

        search_payload = {
            "vector": vector,
            "limit": 5,
            "with_payload": True
        }

        # We perform a manual POST request to Qdrant
        # This works 100% of the time, regardless of library version
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
                json=search_payload,
                headers={"api-key": QDRANT_KEY},
                timeout=10.0
            )
            response.raise_for_status()  # Check for errors
            search_result = response.json()["result"]

        results = []
        for hit in search_result:
            # When using raw HTTP, the structure is a dictionary (hit['payload']), not an object (hit.payload)
            payload = hit.get("payload", {})
            results.append({
                "product_name": payload.get("product_name", "Inconnu"),
                "price": payload.get("price", 0),
                "image_url": payload.get("image_url", ""),
                "score": hit.get("score", 0)
            })

        return {"detected_query": detected_content, "results": results}

    except Exception as e:
        print(f"❌ Erreur Serveur: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)