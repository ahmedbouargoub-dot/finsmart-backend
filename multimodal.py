import torch
from sentence_transformers import SentenceTransformer
from PIL import Image
import whisper
import os


class FinsmartBrain:
    def __init__(self):
        print("🧠 Chargement du modèle Multimodal (CLIP)...")
        # CLIP encode le Texte et l'Image dans le même espace vectoriel (512 dimensions)
        # C'est ce qui permet de chercher une image avec du texte et vice-versa.
        self.clip_model = SentenceTransformer('clip-ViT-B-32')

        print("🎙️ Chargement du modèle Vocal (Whisper)...")
        # 'base' est un bon équilibre entre rapidité et précision pour un PC standard.
        # Vous pouvez utiliser 'tiny' si votre PC est lent, ou 'small' s'il est puissant.
        self.whisper_model = whisper.load_model("base")

    def process_text(self, text: str):
        """
        Transforme une phrase (ex: 'Ordinateur portable') en vecteur numérique.
        """
        # .tolist() est important pour que Qdrant accepte le format
        vector = self.clip_model.encode(text)
        return vector.tolist()

    def process_image(self, image_input):
        """
        Transforme une image (fichier ouvert) en vecteur numérique.
        """
        # On s'assure que c'est bien une image PIL
        if not isinstance(image_input, Image.Image):
            image = Image.open(image_input)
        else:
            image = image_input

        vector = self.clip_model.encode(image)
        return vector.tolist()

    def process_audio(self, audio_path: str):
        """
        1. Transcrit l'audio en texte (Whisper)
        2. Transforme ce texte en vecteur (CLIP)
        """
        print(f"🎧 Transcription de l'audio : {audio_path}")

        # Whisper lit le fichier audio et extrait le texte
        result = self.whisper_model.transcribe(audio_path)
        transcribed_text = result["text"]
        print(f"   -> Texte détecté : '{transcribed_text}'")

        # On utilise CLIP pour vectoriser ce texte
        # (Car Qdrant contient des vecteurs CLIP, donc on doit comparer des pommes avec des pommes)
        return self.process_text(transcribed_text), transcribed_text


# --- Bloc de test (pour vérifier que ça marche sans lancer le serveur) ---
if __name__ == "__main__":
    print("--- TEST UNITAIRE ---")
    brain = FinsmartBrain()

    # Test Texte
    vec = brain.process_text("Test")
    print(f"Dimension vecteur texte : {len(vec)}")  # Doit afficher 512

    print("✅ Le fichier multimodal.py fonctionne !")