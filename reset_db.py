from qdrant_client import QdrantClient
from qdrant_client.http import models

# --- VOS IDENTIFIANTS INTÉGRÉS ---
# --- VOS IDENTIFIANTS INTÉGRÉS ---
QDRANT_URL = "https://42cdf35b-ac5d-474a-a783-c96835d3e3cb.europe-west3-0.gcp.cloud.qdrant.io"
QDRANT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.uimBBa-5yUfQF1EQa61Ikd-03AQKK9rNQ_h5VsIQmHw"
COLLECTION_NAME = "finsmart_products"
print(f"🔌 Tentative de connexion à : {QDRANT_URL}...")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)

# 1. Suppression de l'ancienne collection
try:
    client.delete_collection(COLLECTION_NAME)
    print(f"🗑️ Ancienne collection '{COLLECTION_NAME}' supprimée.")
except Exception as e:
    print(f"Info: Pas d'ancienne collection ou erreur mineure ({e})")

# 2. Création de la nouvelle collection (Taille 512 pour CLIP)
try:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=512,  # <--- INDISPENSABLE POUR CLIP
            distance=models.Distance.COSINE
        )
    )
    print("✅ Nouvelle collection Multimodale (Size: 512) créée avec succès !")
    print("🚀 La base est prête à recevoir les données.")

except Exception as e:
    print(f"❌ Erreur critique lors de la création : {e}")
    print("Vérifiez que votre clé API est valide et que l'URL est correcte.")