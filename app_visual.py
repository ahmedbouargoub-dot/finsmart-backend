import streamlit as st
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Finsmart - Shopping Intelligent",
    page_icon="🛍️",
    layout="wide"
)

# L'adresse de votre serveur (main.py)
API_URL = "http://127.0.0.1:8000/search_multimodal"

# --- BARRE LATÉRALE (VOTRE BUDGET) ---
with st.sidebar:
    st.title("💰 Mon Portefeuille")
    st.write("Définissez votre budget max. L'IA filtrera les résultats pour vous.")

    # Sélecteur de budget (en Roupies ₹ car votre CSV est indien, modifiable en €)
    my_budget = st.number_input(
        "Mon Budget Maximum (₹)",
        min_value=0,
        value=20000,
        step=500
    )

    st.divider()
    st.info("🟢 Mode : Local & Gratuit\n(Pas d'API OpenAI utilisée)")

# --- EN-TÊTE ---
st.title("🛍️ Finsmart : Le Shopping du Futur")
st.markdown("""
Trouvez le produit parfait en utilisant :
* 📝 **Du Texte** (Description précise)
* 📷 **Une Image** (Photo d'un produit que vous aimez)
* 🎙️ **Votre Voix** (Dites ce que vous voulez)
""")

st.divider()

# --- SÉLECTION DU MODE ---
mode = st.radio(
    "Comment voulez-vous chercher ?",
    ["📝 Recherche Texte", "📷 Recherche Image", "🎙️ Recherche Vocale"],
    horizontal=True
)

# Variables pour stocker la requête avant l'envoi
payload = {}
files = None
search_triggered = False

# --- GESTION DES ENTRÉES ---
if mode == "📝 Recherche Texte":
    col1, col2 = st.columns([3, 1])
    with col1:
        user_text = st.text_input("Décrivez le produit recherché :",
                                  placeholder="Ex: Casque bluetooth noir avec bonnes basses")
    with col2:
        st.write("")  # Espacement
        st.write("")
        if st.button("🔍 Rechercher", use_container_width=True):
            if user_text:
                payload = {"input_type": "text", "query_text": user_text}
                search_triggered = True
            else:
                st.warning("Veuillez écrire quelque chose.")

elif mode == "📷 Recherche Image":
    uploaded_file = st.file_uploader("Envoyez une photo d'un produit similaire", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        # Afficher l'image envoyée
        st.image(uploaded_file, caption="Votre image source", width=200)

        if st.button("🔍 Trouver des produits similaires"):
            # On prépare le fichier pour l'envoi
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            payload = {"input_type": "image"}
            search_triggered = True

elif mode == "🎙️ Recherche Vocale":
    st.write("Enregistrez votre demande (ex: avec l'enregistreur Windows) et déposez le fichier ici.")
    audio_file = st.file_uploader("Fichier Audio (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a"])

    if audio_file:
        st.audio(audio_file)
        if st.button("🗣️ Analyser ma voix"):
            files = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type)}
            payload = {"input_type": "audio"}
            search_triggered = True

# --- AFFICHAGE DES RÉSULTATS ---
if search_triggered:
    st.divider()
    with st.spinner("🧠 Le cerveau Finsmart analyse votre demande..."):
        try:
            # Envoi de la requête au serveur backend (main.py)
            response = requests.post(API_URL, data=payload, files=files)

            if response.status_code == 200:
                data = response.json()

                # Feedback sur ce que l'IA a compris
                st.success(f"🎯 J'ai compris : **{data['detected_query']}**")

                results = data['results']

                if not results:
                    st.warning("Aucun produit similaire trouvé.")
                else:
                    st.subheader(f"Voici les {len(results)} meilleurs résultats :")

                    # Affichage en grille (3 colonnes)
                    cols = st.columns(3)

                    for idx, item in enumerate(results):
                        with cols[idx % 3]:  # Distribution cyclique dans les colonnes
                            # -- LOGIQUE INTELLIGENTE GRATUITE --
                            # On compare le prix au budget sans IA payante
                            price = float(item['price'])
                            product_name = item['product_name']
                            image_url = item['image_url']

                            # Cadre visuel
                            with st.container(border=True):
                                # Image du produit
                                if image_url and str(image_url) != "nan":
                                    try:
                                        st.image(image_url, use_container_width=True)
                                    except:
                                        st.text("Image non disponible")

                                # Nom du produit (tronqué si trop long)
                                clean_name = (product_name[:60] + '...') if len(product_name) > 60 else product_name
                                st.markdown(f"**{clean_name}**")

                                # Analyse du prix vs Budget
                                if price == 0:
                                    st.markdown("### Prix Inconnu")
                                    st.info("❓ Vérifier sur le site")
                                elif price <= my_budget:
                                    # C'est dans le budget !
                                    st.markdown(f"### <span style='color:green'>₹{price:,.0f}</span>",
                                                unsafe_allow_html=True)
                                    st.success("✅ Excellente Affaire !")
                                else:
                                    # C'est trop cher
                                    diff = price - my_budget
                                    st.markdown(f"### <span style='color:red'>₹{price:,.0f}</span>",
                                                unsafe_allow_html=True)
                                    st.error(f"❌ Hors budget (+{diff:,.0f}₹)")

                                # Score de similarité (optionnel)
                                st.caption(f"Pertinence : {int(item['score'] * 100)}%")

            else:
                st.error(f"Erreur du serveur : {response.status_code}")
                st.write(response.text)

        except requests.exceptions.ConnectionError:
            st.error("🚫 Impossible de connecter au serveur !")
            st.info("👉 Avez-vous bien lancé 'python main.py' dans un autre terminal ?")
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")