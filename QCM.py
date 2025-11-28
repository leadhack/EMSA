import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import csv

# ----------------------------------------------------
# FICHIER COMPLET STREAMLIT — QCM IF / ELSE
# - Saisie nom / prénom
# - 10 questions
# - Sauvegarde CSV
# - Espace Admin protégé
# ----------------------------------------------------

CSV_FILE = Path("resultats_qcm.csv")

st.set_page_config(page_title="QCM Algorithmique — IF/ELSE", layout="centered")
st.title("QCM Algorithmique — IF / ELSE")
st.write("Complète ton nom, réponds aux questions, valide, et sauvegarde ton score.")

# ----------------------------
# Liste des questions
# ----------------------------
QUESTIONS = [
    {
        "q": "1) Que fait une structure IF ?",
        "opts": ["Répète une instruction", "Effectue un choix selon une condition", "Tri des éléments", "Arrête l'algorithme"],
        "a": 1,
    },
    {
        "q": "2) Syntaxe correcte pour vérifier si n est pair (pseudo-code) :",
        "opts": ["SI n / 2 = 0 ALORS", "SI n % 2 = 0 ALORS", "SI n = 2 ALORS", "SI n = 0 ALORS"],
        "a": 1,
    },
    {
        "q": "3) Quelle condition est vraie ?",
        "opts": ["5 < 3", "10 == 5", "7 > 2", "4 != 4"],
        "a": 2,
    },
    {
        "q": "4) Que fait ELSE ?",
        "opts": ["Teste une autre condition", "S'exécute si IF est faux", "Lance une boucle", "Compare deux valeurs"],
        "a": 1,
    },
    {
        "q": "5) Expression équivalente à 'x n'est pas entre 5 et 10 inclus' :",
        "opts": ["x < 5 OU x > 10", "x <= 5 ET x >= 10", "x > 5 ET x < 10", "x = 5 OU x = 10"],
        "a": 0,
    },
    {
        "q": "6) Que signifie 'NON (a > b)' ?",
        "opts": ["a > b", "a <= b", "a < b", "a >= b"],
        "a": 1,
    },
    {
        "q": "7) Pour a=3, b=4, que donne : SI a+b > 10 ALORS ... SINON SI a*b > 10 ALORS 'B' SINON 'C' ?",
        "opts": ["A", "B", "C", "Erreur"],
        "a": 2,
    },
    {
        "q": "8) Condition correcte pour afficher OK si x est pair ET strictement > 0 :",
        "opts": ["x % 2 = 0 ET x > 0", "x % 2 = 0 OU x > 0", "x > 0", "x % 2 != 0 ET x > 0"],
        "a": 0,
    },
    {
        "q": "9) Résultat si y=0 ? SI y=0 ALORS SI y<1 ALORS 'A' SINON 'B' FIN SINON 'C' FIN",
        "opts": ["A", "B", "C", "Rien"],
        "a": 0,
    },
    {
        "q": "10) Quelle expression est fausse ?",
        "opts": ["5 < 6 OU 3 > 1", "(10 > 5) ET (8 < 2)", "NON (4 < 3)", "7 != 7 OU 2 < 3"],
        "a": 1,
    },
]

# ----------------------------------------------------
# Navigation
# ----------------------------------------------------
page = st.sidebar.radio("Navigation", ["Passer le QCM", "Admin"])

# ----------------------------------------------------
# PAGE : PASSER LE QCM
# ----------------------------------------------------
if page == "Passer le QCM":

    st.subheader("Tes informations")

    with st.form(key="qcm_form"):
        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")

        st.write("---")
        st.subheader("Questions")

        answers = []
        for i, item in enumerate(QUESTIONS):
            ans = st.radio(item['q'], item['opts'], key=f"q{i}")
            answers.append(item['opts'].index(ans))

        submit = st.form_submit_button("Valider")

    # ---------------------------
    # Traitement APRES le form
    # ---------------------------
    if submit:
        if not nom.strip() or not prenom.strip():
            st.error("Veuillez saisir votre nom et prénom.")
        else:
            correct = sum(1 for i, it in enumerate(QUESTIONS) if answers[i] == it['a'])
            total = len(QUESTIONS)
            percent = round(correct * 100 / total, 1)

            st.success(f"{prenom} {nom} — Score : {correct}/{total} ({percent}%)")

            row = {
                "prenom": prenom,
                "nom": nom,
                "score": correct,
                "total": total,
                "percent": percent,
                "date": datetime.now().isoformat(timespec='seconds')
            }

            # Sauvegarde CSV
            write_header = not CSV_FILE.exists()
            with CSV_FILE.open("a", newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                if write_header:
                    writer.writeheader()
                writer.writerow(row)

            st.info("Résultat enregistré.")

            # Téléchargement personnel
            df_person = pd.DataFrame([row])
            csv_person = df_person.to_csv(index=False).encode('utf-8')

            st.download_button(
                "Télécharger mon résultat (CSV)",
                csv_person,
                file_name=f"resultat_{nom}_{prenom}.csv"
            )

# ----------------------------------------------------
# PAGE : ADMIN
# ----------------------------------------------------
elif page == "Admin":
    st.subheader("Espace Admin")
    st.write("⚠ Accès protégé — entrez le mot de passe")

    admin_password = st.text_input("Mot de passe", type="password")

    # Lecture mot de passe dans secrets si défini
    try:
        secret_pw = st.secrets.get("ADMIN_PASSWORD", None)
    except Exception:
        secret_pw = None

    pw_ok = False
    if secret_pw:
        pw_ok = (admin_password == secret_pw)
    else:
        pw_ok = (admin_password == "admin")  # mode local

    if pw_ok:
        st.success("Accès accordé ✔")

        if CSV_FILE.exists():
            df = pd.read_csv(CSV_FILE)
            st.write(f"Nombre de résultats enregistrés : {len(df)}")

            st.dataframe(df)

            st.write("---")
            st.subheader("Statistiques")
            st.metric("Moyenne des scores (%)", round(df['percent'].mean(), 1))
            st.metric("Score maximum", int(df['score'].max()))

            with CSV_FILE.open("rb") as f:
                st.download_button("Télécharger tous les résultats (CSV)", f, file_name="resultats_qcm.csv")
        else:
            st.info("Aucun résultat pour le moment.")

    else:
        if admin_password:
            st.error("Mot de passe incorrect.")
        else:
            st.info("Veuillez entrer le mot de passe.")

# ----------------------------------------------------
# Footer
# ----------------------------------------------------
st.write("---")
st.caption("Créé avec ❤️ — Partage via Streamlit Cloud pour obtenir un lien public.")