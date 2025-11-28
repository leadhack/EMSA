import streamlit as st
import gspread
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials

# -----------------------------
# CONFIG GOOGLE SHEETS
# -----------------------------

SHEET_NAME = "QCM_Algo_Resultats"

# Connexion via secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# -----------------------------
# QUESTIONS DU QCM
# -----------------------------
QUESTIONS = [
    {
        "q": "Que fait ce code ?\nIF age >= 18 THEN afficher 'majeur' ELSE afficher 'mineur'",
        "opts": ["Teste si l’âge est supérieur à 18", "Teste si l’âge est inférieur à 18", "Teste si l’âge est égal à 18"],
        "a": 0
    },
    {
        "q": "Dans un IF/ELSE, que signifie ELSE ?",
        "opts": ["Sinon", "Et si", "Toujours"],
        "a": 0
    },
    {
        "q": "Que donnera : IF x = 5 THEN y = 10 ELSE y = 0 (avec x = 3)",
        "opts": ["y = 10", "y = 0", "Erreur"],
        "a": 1
    }
]

# -----------------------------
# PAGE
# -----------------------------
st.set_page_config(page_title="QCM Algo", page_icon="🧠")

menu = st.sidebar.radio("Navigation", ["Passer le QCM", "Admin"])

# =============================
# PAGE QCM ÉTUDIANT
# =============================
if menu == "Passer le QCM":

    st.title("🧠 QCM Algorithme — IF / ELSE")

    with st.form("qcm_form"):
        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")

        answers = []
        st.write("### Questions :")
        for i, item in enumerate(QUESTIONS):
            rep = st.radio(item["q"], item["opts"], key=f"q{i}")
            answers.append(item["opts"].index(rep))

        submit = st.form_submit_button("Valider mes réponses")

    # Une fois validé
    if submit:
        if nom.strip() == "" or prenom.strip() == "":
            st.error("Veuillez remplir votre nom et prénom.")
            st.stop()

        correct = sum(1 for i, it in enumerate(QUESTIONS) if answers[i] == it["a"])
        total = len(QUESTIONS)
        percent = round(correct / total * 100, 1)

        st.success(f"Résultat : {correct}/{total} — {percent}%")

        # Enregistrement dans Google Sheets
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [now, nom, prenom, correct, total, percent]
        sheet.append_row(row)

        st.info("Votre résultat a été enregistré dans le système centralisé ✔")

        # Téléchargement résultat perso
        df = pd.DataFrame([{
            "date": now, "nom": nom, "prenom": prenom,
            "score": correct, "total": total, "percent": percent
        }])

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Télécharger mon résultat",
            csv,
            file_name=f"resultat_{nom}_{prenom}.csv",
            mime="text/csv"
        )

# =============================
# PAGE ADMIN
# =============================
if menu == "Admin":

    st.title("🔐 Tableau de bord Admin")

    # Mot de passe admin (mettre dans secrets)
    ADMIN_PASSWORD = st.secrets.get("admin_password", "")

    pwd = st.text_input("Mot de passe admin :", type="password")

    if pwd != ADMIN_PASSWORD:
        st.warning("Mot de passe incorrect.")
        st.stop()

    st.success("Accès admin accordé ✔")

    # Charger toutes les données Google Sheets
    data = sheet.get_all_records()

    if not data:
        st.info("Aucun résultat pour le moment.")
        st.stop()

    df = pd.DataFrame(data)

    st.subheader("Résultats enregistrés :")
    st.dataframe(df)

    st.download_button(
        "⬇ Télécharger tous les résultats (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        "export_complet.csv",
        mime="text/csv"
    )
