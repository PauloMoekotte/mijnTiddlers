import streamlit as st

# Structuur gebaseerd op https://roadmap.sh/ai-data-scientist
roadmap_modules = {
    "Introductie": {
        "text": """
Welkom bij de interactieve e-cursus **AI & Data Science**!  
Deze cursus volgt de [AI and Data Scientist Roadmap](https://roadmap.sh/ai-data-scientist) van [Roadmap.sh](https://roadmap.sh/).  
Je maakt kennis met de belangrijkste stappen, van wiskunde tot machine learning, en van data engineering tot deep learning.
""",
    },
    "Mathematics Fundamentals": {
        "text": """
#### Mathematics Fundamentals  
Een stevige basis in wiskunde is essentieel voor AI & Data Science. Focus op:
- Lineaire algebra (vectoren, matrices)
- Statistiek & kansrekening
- Calculus (afgeleiden, integralen)

**Bronnen:**
- [Khan Academy: Statistics](https://www.khanacademy.org/math/statistics-probability)
- [Essence of Linear Algebra (YouTube)](https://www.youtube.com/watch?v=kjBOesZCoqc)
""",
        "quiz": [
            {
                "vraag": "Wat is de determinant van de matrix [[1,2],[3,4]]?",
                "opties": ["-2", "2", "4", "-4"],
                "antwoord": "-2"
            }
        ]
    },
    "Programming: Python & Tools": {
        "text": """
#### Programming: Python & Tools  
Leer de basis van Python, de standaardtaal voor data science.  
Belangrijke libraries: `numpy`, `pandas`, `matplotlib`, `scikit-learn`.

**Bronnen:**
- [Python.org Tutorials](https://docs.python.org/3/tutorial/)
- [Numpy Quickstart](https://numpy.org/doc/stable/user/quickstart.html)
- [Pandas Tutorials](https://pandas.pydata.org/docs/getting_started/index.html)
""",
        "code": """import numpy as np
a = np.array([1, 2, 3])
print("Gemiddelde:", np.mean(a))
""",
        "quiz": [
            {
                "vraag": "Met welke library kun je dataframe-operaties doen in Python?",
                "opties": ["matplotlib", "numpy", "pandas", "scipy"],
                "antwoord": "pandas"
            }
        ]
    },
    "Data Collection & Cleaning": {
        "text": """
#### Data Collection & Cleaning  
Leren omgaan met datasets: importeren, inspecteren & opschonen (missende waarden, outliers).

**Bronnen:**
- [Data Cleaning with Pandas and NumPy](https://realpython.com/python-data-cleaning-numpy-pandas/)
""",
        "code": """import pandas as pd
data = {'leeftijd': [21, None, 35, 19]}
df = pd.DataFrame(data)
df_filled = df.fillna(df['leeftijd'].mean())
print(df_filled)
""",
        "quiz": [
            {
                "vraag": "Hoe vul je ontbrekende waarden in een pandas DataFrame met het gemiddelde?",
                "opties": [
                    "df.fillna(df.mean())", 
                    "df.replace(df.mean())", 
                    "df.fillna(mean)", 
                    "df.dropna()"
                ],
                "antwoord": "df.fillna(df.mean())"
            }
        ]
    },
    "Exploratory Data Analysis (EDA)": {
        "text": """
#### Exploratory Data Analysis (EDA)  
Analyseer en visualiseer data om patronen te ontdekken.

**Bronnen:**
- [EDA met Pandas en Matplotlib](https://www.datacamp.com/tutorial/exploratory-data-analysis-python)
""",
        "code": """import pandas as pd
import matplotlib.pyplot as plt
df = pd.DataFrame({'a': [1,2,3,4],'b':[4,3,2,1]})
df.plot(kind='bar')
plt.title("Voorbeeld barplot")
plt.show()
""",
        "quiz": [
            {
                "vraag": "Welke plot is het meest geschikt voor een variabeleverdeling?",
                "opties": ["Scatterplot", "Barplot", "Histogram", "Lijndiagram"],
                "antwoord": "Histogram"
            }
        ]
    },
    "Machine Learning Basics": {
        "text": """
#### Machine Learning Basics  
Leer de kernbegrippen: supervised/unsupervised learning, classificatie, regressie.

**Bronnen:**
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
""",
        "code": """from sklearn.linear_model import LinearRegression
import numpy as np

X = np.array([[1],[2],[3]])
y = np.array([2,4,6])
model = LinearRegression().fit(X, y)
print("Voorspelling voor 4:", model.predict([[4]]))
""",
        "quiz": [
            {
                "vraag": "Wat is een voorbeeld van supervised learning?",
                "opties": ["KMeans clustering", "Linear Regression", "Principal Component Analysis", "t-SNE"],
                "antwoord": "Linear Regression"
            }
        ]
    },
    "Specialisaties & Vervolg": {
        "text": """
#### Specialisaties & Vervolg  
Verdiep je verder in:
- Deep Learning (neural networks)
- NLP, Computer Vision
- Data Engineering & Big Data
- Model deployment

**Bronnen:**
- [Deep Learning Specialization (Coursera)](https://www.coursera.org/specializations/deep-learning)
- [Full Roadmap](https://roadmap.sh/ai-data-scientist)
""",
    }
}

st.set_page_config(page_title="AI & Data Science e-Cursus", layout="centered")
st.title("🤖 AI & Data Science e-Cursus volgens de Roadmap")

# Navigatie
pagina_lijst = list(roadmap_modules.keys())
pagina = st.sidebar.radio("Ga naar module:", pagina_lijst)

mod = roadmap_modules[pagina]
st.header(pagina)
st.markdown(mod["text"])

if "code" in mod:
    st.subheader("Probeer de code zelf uit:")
    code_input = st.text_area("Schrijf of wijzig de code:", mod["code"], height=150, key=pagina)
    st.code(code_input, language="python")
    st.info("Let op: Uitvoeren van willekeurige Python-code is in Streamlit Cloud gelimiteerd.")

if "quiz" in mod:
    st.subheader("Quiz")
    score = 0
    for i, q in enumerate(mod["quiz"]):
        antwoord = st.radio(q["vraag"], q["opties"], key=f"{pagina}_quiz_{i}")
        if antwoord == q["antwoord"]:
            st.success("Juist!")
            score += 1
        elif antwoord:
            st.warning("Onjuist.")
    st.write(f"**Je score: {score} van {len(mod['quiz'])}**")

st.sidebar.markdown("[Bekijk de volledige roadmap](https://roadmap.sh/ai-data-scientist)")

# Suggestie: voeg een 'voortgangsbalk' toe of uitbreiden met meer deelmodules per hoofdstuk.
