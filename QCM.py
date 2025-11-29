# https://docs.google.com/spreadsheets/d/1PnVhcuq-bC9QOowTO8evBCFFMuqWC9MGsPzwHfQvgWI/edit?gid=0#gid=0
#https://qcm-emsa-algorithme.streamlit.app/
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
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
client = gspread.authorize(creds)

# Feuille résultats
try:
    sheet_results = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"Erreur lors de l'ouverture de la feuille résultats : {e}")

# Feuille questions
try:
    questions_sheet = client.open(SHEET_NAME).worksheet("Questions")
except Exception as e:
    questions_sheet = None
    st.error(f"Erreur lors de l'ouverture de la feuille questions : {e}")

# -----------------------------
# FONCTION POUR CHARGER QUESTIONS
# -----------------------------
def load_questions():
    questions = []
    if questions_sheet:
        questions_data = questions_sheet.get_all_records()
        for row in questions_data:
            try:
                q = row['question']
                opts = [row['option1'], row['option2'], row['option3'], row['option4']]
                correct_idx = int(row['correct_option'])
                questions.append({"q": q, "opts": opts, "a": correct_idx})
            except Exception:
                continue
    return questions

# -----------------------------
# PAGE
# -----------------------------
st.set_page_config(page_title="QCM Algo", page_icon="🧠")
menu = st.sidebar.radio("Navigation", ["Passer le QCM", "Admin"])

# =============================
# PAGE QCM ÉTUDIANT
# =============================
if menu == "Passer le QCM":
    QUESTIONS = load_questions()
    st.title("🧠 QCM Algorithme — IF / ELSE")

    if not QUESTIONS:
        st.warning("Aucune question disponible pour le moment.")
    else:
        with st.form("qcm_form"):
            nom = st.text_input("Nom")
            prenom = st.text_input("Prénom")
            answers = []

            st.write("### Questions :")
            for i, item in enumerate(QUESTIONS):
                rep = st.radio(item["q"], item["opts"], key=f"q{i}")
                try:
                    answers.append(item["opts"].index(rep))
                except ValueError:
                    answers.append(-1)  # valeur par défaut si réponse non trouvée

            submit = st.form_submit_button("Valider mes réponses")

        if submit:
            if not nom.strip() or not prenom.strip():
                st.error("Veuillez remplir votre nom et prénom.")
                st.stop()

            correct = sum(1 for i, it in enumerate(QUESTIONS) if answers[i] == it["a"])
            total = len(QUESTIONS)
            percent = round(correct / total * 100, 1)

            st.success(f"Résultat : {correct}/{total} — {percent}%")

            # Enregistrement dans Google Sheets résultats
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [now, nom, prenom, correct, total, percent]
            try:
                sheet_results.append_row(row)
                st.info("Votre résultat a été enregistré dans le système centralisé ✔")
            except Exception as e:
                st.error(f"Erreur lors de l'enregistrement : {e}")

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

    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    def connect_admin():
        st.session_state.admin_authenticated = True

    def disconnect_admin():
        st.session_state.admin_authenticated = False

    # -----------------------------
    # Si admin connecté
    # -----------------------------
    if st.session_state.admin_authenticated:
        # Bouton déconnexion
        st.button("🔒 Se déconnecter", on_click=disconnect_admin)

        st.success("Accès admin accordé ✔")

        # Actions Admin
        action = st.radio("Action :", ["Voir résultats", "Gérer questions"], key="admin_action")

        if action == "Voir résultats":
            data = sheet_results.get_all_records()
            if not data:
                st.info("Aucun résultat pour le moment.")
            else:
                df = pd.DataFrame(data)
                st.subheader("Résultats enregistrés :")
                st.dataframe(df)
                st.download_button(
                    "⬇ Télécharger tous les résultats (CSV)",
                    df.to_csv(index=False).encode("utf-8"),
                    "export_complet.csv",
                    mime="text/csv"
                )

        elif action == "Gérer questions":
            questions_data = questions_sheet.get_all_records() if questions_sheet else []
            sub_action = st.radio("Action :", ["Rechercher une question", "Ajouter une question"], key="sub_action")

            if sub_action == "Rechercher une question":
                recherche = st.text_input("Mot-clé ou question", key="search_q")
                if recherche:
                    filtered = [q for q in questions_data if recherche.lower() in q['question'].lower()]
                    for q in filtered:
                        st.write(f"**Q :** {q['question']}")
                        st.write(f"Options : {q['option1']}, {q['option2']}, {q['option3']}, {q['option4']}")
                        st.write(f"Réponse correcte : option {q['correct_option']}")

            elif sub_action == "Ajouter une question":
                q_text = st.text_area("Question", key="new_q")
                opt1 = st.text_input("Option 1", key="new_opt1")
                opt2 = st.text_input("Option 2", key="new_opt2")
                opt3 = st.text_input("Option 3", key="new_opt3")
                opt4 = st.text_input("Option 4", key="new_opt4")
                correct_opt = st.selectbox("Réponse correcte (numéro 0-3)", [0, 1, 2, 3], key="new_correct")

                if st.button("Ajouter cette question", key="add_q"):
                    if all([q_text.strip(), opt1.strip(), opt2.strip(), opt3.strip(), opt4.strip()]):
                        new_row = [q_text, opt1, opt2, opt3, opt4, str(correct_opt)]
                        questions_sheet.append_row(new_row)
                        st.success("Question ajoutée avec succès.")
                    else:
                        st.error("Veuillez remplir tous les champs.")

    # -----------------------------
    # Si admin non connecté
    # -----------------------------
    else:
        pwd = st.text_input("Mot de passe admin :", type="password", key="pwd_input")
        st.button("Se connecter", on_click=connect_admin)
