import streamlit as st
import sqlite3
import hashlib
import time
import requests
import cv2
import numpy as np
from ultralytics import YOLO
import speech_recognition as sr

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Finsmart AI | Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de l'API (Backend)
API_URL = "http://127.0.0.1:8000/search_multimodal"

# --- TAUX DE CHANGE ---
CONVERSION_RATE = 0.011


# --- 2. CHARGEMENT MODÈLE YOLO ---
@st.cache_resource
def load_vision_model():
    try:
        return YOLO("yolov8m.pt")
    except Exception as e:
        st.error(f"Erreur YOLO: {e}")
        return None


vision_model = load_vision_model()


# --- 3. FONCTION VOCALE (Local / Micro) ---
def recognize_speech():
    """Écoute le microphone et retourne le texte (Commande Vocale)"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.toast("🎤 Parlez maintenant...", icon="🎙️")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            st.toast("⏳ Analyse...", icon="🔄")
            text = recognizer.recognize_google(audio, language="fr-FR")
            return text
        except Exception:
            return None


# --- 4. GESTION BASE DE DONNÉES (AUTH) ---
def init_db():
    conn = sqlite3.connect('finsmart_users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable_v2(username TEXT, email TEXT, password TEXT, usertype TEXT)')
    conn.commit()
    conn.close()


def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text


def add_userdata(username, email, password, usertype):
    conn = sqlite3.connect('finsmart_users.db')
    c = conn.cursor()
    c.execute('INSERT INTO userstable_v2(username, email, password, usertype) VALUES (?,?,?,?)',
              (username, email, make_hashes(password), usertype))
    conn.commit()
    conn.close()


def login_check(email, password):
    conn = sqlite3.connect('finsmart_users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable_v2 WHERE email = ?', (email,))
    data = c.fetchall()
    conn.close()
    if data and check_hashes(password, data[0][2]):
        return data[0][0], data[0][3]
    return None, None


init_db()

# --- 5. STYLE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
    .stApp { background: radial-gradient(circle at 10% 20%, #0f172a 0%, #1e293b 90%); font-family: 'Outfit', sans-serif; color: white; }
    [data-testid="stSidebar"] { background-color: #0b1120 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    .stTextInput input, .stNumberInput input { background-color: #1e293b !important; color: #38bdf8 !important; border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 10px; }
    [data-testid="stFileUploader"] { background-color: rgba(30, 41, 59, 0.5); border-radius: 10px; padding: 10px; }
    .glass-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(14px); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); padding: 20px; margin-bottom: 20px; transition: transform 0.2s; }
    .glass-card:hover { transform: translateY(-5px); border-color: #38bdf8; }
    div.stButton > button { background: linear-gradient(90deg, #2563eb 0%, #06b6d4 100%); border: none; color: white !important; border-radius: 12px; font-weight: bold; width: 100%; padding: 0.5rem 1rem; }
    div.stButton > button:hover { opacity: 0.9; }
    .price-tag { font-size: 1.4rem; font-weight: 800; color: #fbbf24 !important; } 
    .badge-ok { background: rgba(34, 197, 94, 0.2); color: #4ade80 !important; padding: 4px 8px; border-radius: 10px; font-size: 0.8em; border: 1px solid #4ade80; }
    .badge-warn { background: rgba(239, 68, 68, 0.2); color: #f87171 !important; padding: 4px 8px; border-radius: 10px; font-size: 0.8em; border: 1px solid #f87171; }
    .img-box { width: 100%; height: 180px; overflow: hidden; border-radius: 10px; margin-bottom: 10px; background: #000; display: flex; align-items: center; justify-content: center; }
    .img-box img { max-width: 100%; max-height: 100%; object-fit: contain; }
</style>
""", unsafe_allow_html=True)

# --- 6. SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'reg_type' not in st.session_state: st.session_state.reg_type = "Personnelle"
if 'num_people' not in st.session_state: st.session_state.num_people = 1
if 'vision_res' not in st.session_state: st.session_state.vision_res = None
if 'audio_res' not in st.session_state: st.session_state.audio_res = None
if 'pack_results' not in st.session_state: st.session_state.pack_results = []
if 'search_text' not in st.session_state: st.session_state.search_text = ""


# --- 7. LOGIQUE MÉTIER ---

def go_to(page):
    st.session_state.page = page
    st.rerun()


def search_api(input_type="text", query_text=None, file=None, category="Tous"):
    data = {"input_type": input_type}
    files = None
    if query_text:
        prompt = f"Product: {query_text}"
        if category and category != "Tous":
            prompt += f", Category: {category}"
        data["query_text"] = prompt
    if file:
        files = {"file": (file.name, file, file.type)}
    try:
        r = requests.post(API_URL, data=data, files=files, timeout=15)
        if r.status_code == 200:
            return r.json().get("results", [])
        else:
            st.error(f"Erreur API ({r.status_code})")
            return []
    except Exception as e:
        st.error(f"Erreur Connexion: {e}")
        return []


def render_card(item, qty, min_p, max_p):
    name = item.get('product_name', 'Produit Inconnu')
    raw_price = float(item.get('price', 0))
    euro_price = raw_price * CONVERSION_RATE
    img = item.get('image_url', '')
    if not img or str(img).lower() == 'nan':
        img = "https://via.placeholder.com/300?text=No+Image"
    total_euro = euro_price * qty
    if min_p <= euro_price <= max_p:
        badge = "<span class='badge-ok'>✅ OK</span>"
    else:
        badge = "<span class='badge-warn'>⚠️ HORS BUDGET</span>"

    st.markdown(f"""
    <div class="glass-card">
        <div class="img-box"><img src="{img}"></div>
        <div style="font-weight:700; font-size:1.1em; height:50px; overflow:hidden; line-height:1.2em; margin-bottom:5px;">{name}</div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="price-tag">{euro_price:,.2f} €</div>
            {badge}
        </div>
        <div style="margin-top:12px; border-top:1px solid rgba(255,255,255,0.1); padding-top:8px; display:flex; justify-content:space-between; color:#94a3b8; font-size:0.9em;">
             <span>Qté: {qty}</span>
             <span style="color:white; font-weight:600;">Total: {total_euro:,.2f} €</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- 8. VUES (PAGES) ---

def view_login():
    _, c2, _ = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><div class='glass-card'><h1 style='text-align:center;'>💎 Finsmart Pro</h1>",
                    unsafe_allow_html=True)
        mode = st.selectbox("Menu", ["Connexion", "Inscription"], label_visibility="collapsed")

        if mode == "Connexion":
            # Correction : Utilisation de keys uniques
            e = st.text_input("Email", key="login_email_input")
            p = st.text_input("Mot de passe", type="password", key="login_pass_input")
            if st.button("Se connecter"):
                u, t = login_check(e, p)
                if u:
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.session_state.reg_type = t
                    st.session_state.num_people = 50 if t == "Entreprise" else 1
                    go_to('dashboard')
                else:
                    st.error("Identifiants incorrects")
        else:
            # Correction : Utilisation de keys uniques
            u = st.text_input("Nom d'utilisateur", key="reg_user_input")
            e = st.text_input("Email", key="reg_email_input")
            p = st.text_input("Mot de passe", type="password", key="reg_pass_input")
            t = st.radio("Type de compte", ["Personnelle", "Entreprise"], horizontal=True, key="reg_type_input")
            if st.button("S'inscrire"):
                if u and e and p:
                    add_userdata(u, e, p, t)
                    # CORRECTION : ACCÈS DIRECT APRÈS INSCRIPTION
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.session_state.reg_type = t
                    st.session_state.num_people = 50 if t == "Entreprise" else 1
                    st.success("Compte créé ! Bienvenue.")
                    time.sleep(1)  # Petit délai visuel
                    go_to('dashboard')
                else:
                    st.warning("Veuillez remplir tous les champs.")
        st.markdown("</div>", unsafe_allow_html=True)


def view_dashboard():
    with st.sidebar:
        st.title(f"👋 {st.session_state.username}")
        st.caption(f"Compte: {st.session_state.reg_type}")
        st.markdown("---")

        st.markdown("### 🔍 Recherche Rapide")
        col_search, col_mic = st.columns([4, 1])
        with col_mic:
            if st.button("🎙️", help="Appuyez et parlez"):
                spoken_text = recognize_speech()
                if spoken_text:
                    st.session_state.search_text = spoken_text
                    st.success(f"🗣️ {spoken_text}")
        with col_search:
            search_query = st.text_input("Mot-clé", value=st.session_state.search_text, placeholder="Ex: Laptop...",
                                         key="dash_search_input")
            if search_query != st.session_state.search_text:
                st.session_state.search_text = search_query

        st.markdown("### 🎚️ Filtres")
        cats = ["Tous", "Computers", "Electronics", "Home", "Clothing", "Kitchen"]
        selected_cat = st.selectbox("Catégorie", cats)

        st.markdown("### 💰 Budget (€)")
        budget = st.slider("Budget Max (Euro)", 0, 1000, (0, 300), step=10)
        min_b, max_b = budget

        st.markdown("---")
        if st.button("Se déconnecter"):
            st.session_state.authenticated = False
            go_to('login')

    t1, t2, t3 = st.tabs(["🛒 Recherche & Achats", "📸 Vision Scanner", "🎙️ Audio Search"])

    with t1:
        if st.session_state.search_text:
            st.markdown(f"### Résultats pour : *{st.session_state.search_text}*")
            results = search_api(input_type="text", query_text=st.session_state.search_text, category=selected_cat)
            if results:
                cols = st.columns(3)
                for i, item in enumerate(results):
                    with cols[i % 3]: render_card(item, 1, min_b, max_b)
            else:
                st.warning("Aucun produit trouvé.")
            st.markdown("---")

        st.markdown("<div class='glass-card'><h3>📦 Générateur de Pack Intelligent</h3>", unsafe_allow_html=True)
        c_qty, c_btn = st.columns([1, 2])
        with c_qty:
            if st.session_state.reg_type == "Entreprise":
                st.session_state.num_people = st.number_input("Nombre d'employés", 10, 10000,
                                                              st.session_state.num_people, 10)
            else:
                st.write("Quantité par produit")
                c_m, c_v, c_p = st.columns([1, 1, 1])
                if c_m.button("➖"): st.session_state.num_people = max(1, st.session_state.num_people - 1)
                c_v.markdown(f"<h3 style='text-align:center; margin:0;'>{st.session_state.num_people}</h3>",
                             unsafe_allow_html=True)
                if c_p.button("➕"): st.session_state.num_people += 1
        with c_btn:
            st.write("&nbsp;")
            if st.button("✨ Générer Pack Automatique"):
                st.session_state.pack_results = []
                targets = ["Product"]
                if "Computers" in selected_cat or "Electronics" in selected_cat:
                    targets = ["Laptop", "Mouse", "Headphones"]
                elif "Clothing" in selected_cat:
                    targets = ["T-shirt", "Jeans", "Shoes"]
                elif "Home" in selected_cat:
                    targets = ["Lamp", "Chair"]
                my_bar = st.progress(0)
                for idx, t in enumerate(targets):
                    found = search_api(input_type="text", query_text=t, category=selected_cat)
                    if found: st.session_state.pack_results.append(found[0])
                    my_bar.progress((idx + 1) / len(targets))
                my_bar.empty()
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.pack_results:
            st.markdown("### Votre Pack Suggéré")
            cols = st.columns(3)
            for i, item in enumerate(st.session_state.pack_results):
                with cols[i % 3]: render_card(item, st.session_state.num_people, min_b, max_b)

    with t2:
        st.markdown("<div class='glass-card'><h3>👁️ Vision Search</h3><p>Analysez une photo ou utilisez la caméra.</p>",
                    unsafe_allow_html=True)
        input_method = st.radio("Source de l'image :", ["📸 Caméra", "📂 Importer une image"], horizontal=True)
        img_file_buffer = None
        if input_method == "📸 Caméra":
            img_file_buffer = st.camera_input("Scanner un objet")
        else:
            img_file_buffer = st.file_uploader("Téléverser une image (JPG, PNG)", type=['png', 'jpg', 'jpeg'])

        if img_file_buffer is not None and vision_model:
            bytes_data = img_file_buffer.getvalue()
            img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            results = vision_model(img)
            annotated_frame = results[0].plot()
            st.image(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB), caption="Analyse IA", use_container_width=True)

            detected_obj = None
            max_conf = 0.0
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    name = vision_model.names[cls_id]
                    if name != "person" and conf > max_conf:
                        max_conf = conf
                        detected_obj = name
            if detected_obj:
                st.success(f"Objet détecté : **{detected_obj.upper()}**")
                if st.button(f"🔍 Rechercher des '{detected_obj}'"):
                    st.session_state.vision_res = search_api(input_type="text", query_text=detected_obj,
                                                             category="Tous")
            else:
                st.warning("Aucun objet clair détecté.")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.vision_res:
            st.markdown("### Résultats Vision")
            cols = st.columns(3)
            for i, item in enumerate(st.session_state.vision_res):
                with cols[i % 3]: render_card(item, 1, 0, 1000000)

    with t3:
        st.markdown(
            "<div class='glass-card'><h3>🎙️ Recherche Audio (Multimodal)</h3><p>Envoyez un fichier audio pour l'analyser.</p>",
            unsafe_allow_html=True)
        audio_file = st.file_uploader("Uploader un fichier audio (WAV, MP3)", type=['wav', 'mp3'], key="audio_uploader")
        if audio_file is not None:
            st.audio(audio_file)
            if st.button("🔍 Analyser l'Audio"):
                with st.spinner("Envoi au Cerveau IA..."):
                    st.session_state.audio_res = search_api(input_type="audio", file=audio_file)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.audio_res:
            st.markdown("### 🎧 Résultats Audio")
            cols = st.columns(3)
            for i, item in enumerate(st.session_state.audio_res):
                with cols[i % 3]: render_card(item, 1, 0, 1000000)


# --- ROUTER ---
if st.session_state.page == 'login':
    view_login()
elif st.session_state.page == 'dashboard':
    if st.session_state.authenticated:
        view_dashboard()
    else:
        go_to('login')
