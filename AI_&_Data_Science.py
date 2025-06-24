import streamlit as st

# Uitgebreide structuur met meer modules en bronnen
roadmap_modules = {
    "Introductie": {
        "text": """
Welkom bij de interactieve e-cursus **AI & Data Science**!  
Deze cursus volgt de [AI and Data Scientist Roadmap](https://roadmap.sh/ai-data-scientist).  
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
- [Paul's Online Math Notes](https://tutorial.math.lamar.edu/)
- [StatQuest (YouTube)](https://www.youtube.com/user/joshstarmer)
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
- [Real Python](https://realpython.com/)
- [W3Schools Python](https://www.w3schools.com/python/)
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
- [Towards Data Science: Data Cleaning](https://towardsdatascience.com/the-ultimate-guide-to-data-cleaning-3969843991d4)
- [Kaggle Datasets](https://www.kaggle.com/datasets)
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
- [Towards Data Science: EDA](https://towardsdatascience.com/exploratory-data-analysis-8fc1cb20fd15)
- [Seaborn Documentation](https://seaborn.pydata.org/)
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
    "Data Visualization": {
        "text": """
#### Data Visualization  
Maak je analyses inzichtelijk met visualisaties.

**Bronnen:**
- [Matplotlib Tutorial](https://matplotlib.org/stable/tutorials/index.html)
- [Seaborn Gallery](https://seaborn.pydata.org/examples/index.html)
- [Plotly Python Open Source Graphing Library](https://plotly.com/python/)
""",
        "code": """import matplotlib.pyplot as plt
import numpy as np
x = np.linspace(0, 10, 100)
y = np.sin(x)
plt.plot(x, y)
plt.title("Sinusgolf")
plt.show()
"""
    },
    "Machine Learning Basics": {
        "text": """
#### Machine Learning Basics  
Leer de kernbegrippen: supervised/unsupervised learning, classificatie, regressie.

**Bronnen:**
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [Coursera: Machine Learning (Andrew Ng)](https://www.coursera.org/learn/machine-learning)
- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
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
    "Deep Learning": {
        "text": """
#### Deep Learning  
Verdiep je in neurale netwerken, deep learning frameworks en toepassingen.

**Bronnen:**
- [Deep Learning Specialization (Coursera)](https://www.coursera.org/specializations/deep-learning)
- [TensorFlow Tutorials](https://www.tensorflow.org/tutorials)
- [PyTorch Tutorials](https://pytorch.org/tutorials/)
- [Fast.ai](https://course.fast.ai/)
""",
    },
    "Natural Language Processing (NLP)": {
        "text": """
#### Natural Language Processing (NLP)  
Verwerken van en inzichten halen uit tekstdata.

**Bronnen:**
- [NLTK Book](https://www.nltk.org/book/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/index)
- [Stanford NLP Course](https://web.stanford.edu/class/cs224n/)
""",
    },
    "Deployment & MLOps": {
        "text": """
#### Deployment & MLOps  
Leer hoe je modellen in productie brengt en onderhoudt.

**Bronnen:**
- [MLflow](https://mlflow.org/docs/latest/index.html)
- [TensorFlow Serving](https://www.tensorflow.org/tfx/guide/serving)
- [AWS Machine Learning Operations](https://aws.amazon.com/mlops/)
- [Full Stack Deep Learning](https://fullstackdeeplearning.com/)
""",
    },
    "Ethics & Responsible AI": {
        "text": """
#### Ethics & Responsible AI  
Begrijp ethische kwesties rond AI & Data Science.

**Bronnen:**
- [Google AI Principles](https://ai.google/responsibilities/responsible-ai-practices/)
- [AI Now Institute](https://ainowinstitute.org/)
- [The Alan Turing Institute: Responsible AI](https://www.turing.ac.uk/research/research-programmes/ai-ethics-and-society)
""",
    },
    "Carrièrepaden in Data Science": {
        "text": """
#### Carrièrepaden in Data Science  
Ontdek verschillende rollen en hoe je verder kunt leren.

**Bronnen:**
- [DataCamp: How to Become a Data Scientist](https://www.datacamp.com/blog/how-to-become-a-data-scientist)
- [Towards Data Science: Data Science Career Guide](https://towardsdatascience.com/data-science-career-paths-2c8f4c4f4c9a)
- [LinkedIn Learning: Data Science Paths](https://www.linkedin.com/learning/paths/advance-your-skills-in-data-science)
""",
    },
  "Specialisaties & Vervolg": {
     "text": """
Hier kun je je verder specialiseren, bijvoorbeeld in computer vision, reinforcement learning, big data, enzovoorts.
"""
     }
