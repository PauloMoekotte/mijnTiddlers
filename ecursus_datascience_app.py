import streamlit as st

# Cursus inhoud
chapters = {
    "Introductie": {
        "text": """
Welkom bij de interactieve Data Science e-cursus! 
In deze cursus leer je de basisprincipes van Data Science, waaronder Python, data analyse, visualisatie en machine learning.
""",
    },
    "Python Basics": {
        "text": """
### Python Basics

Hier leer je over variabelen, types, en eenvoudige bewerkingen.
""",
        "code": """# Probeer het zelf!
a = 5
b = 3
c = a + b
print("De som is:", c)
"""
    },
    "Data Analyse": {
        "text": """
### Data Analyse

We gebruiken pandas om datasets te analyseren.
""",
        "code": """import pandas as pd

data = {'Naam': ['Jan', 'Piet', 'Klaas'],
        'Leeftijd': [23, 35, 45]}
df = pd.DataFrame(data)
print(df.describe())
"""
    },
    "Visualisatie": {
        "text": """
### Visualisatie

We gebruiken matplotlib voor grafieken.
""",
        "code": """import matplotlib.pyplot as plt

x = [1, 2, 3]
y = [10, 20, 15]
plt.plot(x, y)
plt.title("Voorbeeld grafiek")
plt.show()
"""
    },
    "Machine Learning Intro": {
        "text": """
### Machine Learning Intro

Machine learning voorspelt uitkomsten op basis van data.
""",
        "code": """from sklearn.linear_model import LinearRegression
import numpy as np

X = np.array([[1], [2], [3]])
y = np.array([2, 4, 6])
model = LinearRegression()
model.fit(X, y)
print("Voorspelling voor 4:", model.predict([[4]]))
"""
    }
}

quiz = [
    {
        "vraag": "Wat is het resultaat van 2 + 3 * 2?",
        "opties": ["10", "8", "7", "6"],
        "antwoord": "8"
    },
    {
        "vraag": "Welke Python package gebruik je voor dataframes?",
        "opties": ["numpy", "sklearn", "pandas", "matplotlib"],
        "antwoord": "pandas"
    }
]

st.set_page_config(page_title="Data Science e-Cursus", layout="centered")
st.title("📊 Data Science e-Cursus")

# Navigatie
hoofdstukken = list(chapters.keys())
page = st.sidebar.radio("Ga naar hoofdstuk:", hoofdstukken + ["Quiz"])

if page in chapters:
    st.header(page)
    st.markdown(chapters[page]["text"])
    if "code" in chapters[page]:
        st.subheader("Probeer het zelf:")
        code_input = st.text_area("Schrijf of wijzig de code:", chapters[page]["code"], height=150, key=page)
        st.code(code_input, language="python")
        st.info("Let op: Uit veiligheidsredenen kun je in Streamlit Cloud geen willekeurige Python-code uitvoeren.")
elif page == "Quiz":
    st.header("Quiz")
    score = 0
    for i, q in enumerate(quiz):
        st.subheader(f"Vraag {i+1}: {q['vraag']}")
        antwoord = st.radio("Kies het juiste antwoord:", q["opties"], key=f"quiz_{i}")
        if antwoord == q["antwoord"]:
            st.success("Juist!")
            score += 1
        else:
            st.warning("Onjuist.")
    st.write(f"**Je score: {score} van {len(quiz)}**")