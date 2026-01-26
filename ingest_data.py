import pandas as pd
import glob
import os
import re
from qdrant_client import QdrantClient
from qdrant_client.http import models
from core.multimodal import FinsmartBrain

# --- API KEYS ---
QDRANT_URL = "https://42cdf35b-ac5d-474a-a783-c96835d3e3cb.europe-west3-0.gcp.cloud.qdrant.io"
QDRANT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.uimBBa-5yUfQF1EQa61Ikd-03AQKK9rNQ_h5VsIQmHw"
COLLECTION_NAME = "finsmart_products"


def clean_price(price_str):
    if pd.isna(price_str) or str(price_str).strip() == "":
        return 0.0
    try:
        clean_str = re.sub(r'[₹, ]', '', str(price_str))
        return float(clean_str)
    except:
        return 0.0


def ingest_data():
    print("🔌 Connexion à votre Cluster Qdrant...")
    try:
        # --- FIX 1: INCREASED TIMEOUT TO 60 SECONDS ---
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY, timeout=60.0)
        client.get_collections()
        print("✅ Connexion réussie !")
    except Exception as e:
        print(f"❌ Erreur de connexion (Vérifiez la clé) : {e}")
        return

    print("🧠 Chargement du Cerveau Local (CLIP)...")
    brain = FinsmartBrain()

    csv_files = glob.glob(os.path.join("data", "*.csv"))

    if not csv_files:
        print("⚠️ Aucun fichier CSV trouvé dans le dossier 'data/'")
        return

    for file_path in csv_files:
        print(f"📖 Lecture : {file_path}")
        df = pd.read_csv(file_path)
        points = []

        print(f"📊 {len(df)} produits à traiter...")

        for index, row in df.iterrows():
            try:
                p_name = str(row.get('name', 'Inconnu'))
                p_cat = str(row.get('main_category', '')) + " " + str(row.get('sub_category', ''))
                p_img = str(row.get('image', ''))
                raw_price = row.get('discount_price', row.get('actual_price', '0'))
                p_price = clean_price(raw_price)

                text_to_embed = f"{p_name}. Categorie: {p_cat}"
                vector = brain.process_text(text_to_embed)

                points.append(models.PointStruct(
                    id=index,
                    vector=vector,
                    payload={
                        "product_name": p_name,
                        "price": p_price,
                        "image_url": p_img
                    }
                ))
            except Exception as e:
                pass

                # --- FIX 2: SMALLER BATCH SIZE (32 instead of 50) ---
            # This makes uploads lighter and faster, preventing timeouts
            if len(points) >= 32:
                try:
                    client.upsert(collection_name=COLLECTION_NAME, points=points)
                    print(f"📤 Paquet envoyé (Ligne {index})")
                    points = []
                except Exception as e:
                    print(f"⚠️ Petit souci réseau (Upload), on réessaie le paquet... {e}")
                    # Simple retry logic could go here, but usually smaller batches fix it.

        if points:
            try:
                client.upsert(collection_name=COLLECTION_NAME, points=points)
                print("📤 Dernier paquet envoyé.")
            except Exception as e:
                print(f"⚠️ Erreur sur le dernier paquet: {e}")

    print("🚀 Importation terminée vers Qdrant Cloud !")


if __name__ == "__main__":
    ingest_data()