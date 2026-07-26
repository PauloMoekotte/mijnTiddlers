"""
📊 MBO Bekostigingsdashboard - Streamlit App
Upload TBG PDF's en vergelijk automatisch bekostigingsdata
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO
import base64
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="MBO Bekostigingsdashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1e3a5f; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #6b7280; margin-bottom: 2rem; }
    .kpi-card { background: white; border-radius: 12px; padding: 1.5rem; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid; }
    .metric-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; 
                   color: #6b7280; font-weight: 600; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #1f2937; margin-top: 0.3rem; }
    .metric-sub { font-size: 0.85rem; color: #9ca3af; margin-top: 0.2rem; }
    .insight-box { background: #eff6ff; border-left: 4px solid #2E86AB; 
                  padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA EXTRACTION FROM PDF TEXT
# ============================================================
def extract_tbg_data(pdf_text: str, instelling_code: str) -> dict:
    """
    Extract structured TBG data from PDF text content.
    Falls back to manual entry if parsing fails.
    """
    data = {
        "code": instelling_code,
        "naam": "",
        "datum": "",
        "status": "Voorlopige gegevens 2025/2026",
        "entree": {},
        "basisberoeps": {},
        "vak_middenkader_specialisten": {}
    }
    
    # Try to extract institution name
    naam_match = re.search(r'(\d{4,5})\s+([A-Z][a-zA-Z\s&]+?)(?:\s+Postbus|\s+Slingelaan|\s+\d)', pdf_text)
    if naam_match:
        data["naam"] = naam_match.group(2).strip()
    
    # Extract institution shares from cover letter
    entree_ia = re.search(r'entreeopleidingen.*?(\d+[.,]\d+)%', pdf_text, re.DOTALL)
    basis_ia = re.search(r'basisberoepsopleidingen.*?(\d+[.,]\d+)%', pdf_text, re.DOTALL)
    vmks_ia = re.search(r'vak-.*?specialistenopleidingen.*?(\d+[.,]\d+)%', pdf_text, re.DOTALL)
    
    if entree_ia:
        data["entree"]["instellingsaandeel_pct"] = float(entree_ia.group(1).replace(',', '.'))
    if basis_ia:
        data["basisberoeps"]["instellingsaandeel_pct"] = float(basis_ia.group(1).replace(',', '.'))
    if vmks_ia:
        data["vak_middenkader_specialisten"]["instellingsaandeel_pct"] = float(vmks_ia.group(1).replace(',', '.'))
    
    # Extract student values from summary tables
    # Look for the institution's row in national overview tables
    pattern = rf'{instelling_code}.*?(?P<sw>\d{{1,2}}(?:\.\d{{3}})*,\d{{2}}).*?(?P<ia>\d,\d{{2}}%)'
    
    # Extract from detailed calculation pages
    entree_calc = re.search(r'Instellingsaandeel studentenwaarde entreeopleidingen.*?(?P<basis>\d+(?:\.\d{3})*,\d{2}).*?(?P<cf>0,\d+).*?(?P<sw>\d+(?:\.\d{3})*,\d{2})', pdf_text, re.DOTALL)
    if entree_calc:
        data["entree"]["basis_studentenwaarde"] = parse_dutch_number(entree_calc.group("basis"))
        data["entree"]["correctiefactor"] = parse_dutch_number(entree_calc.group("cf"))
        data["entree"]["studentenwaarde"] = parse_dutch_number(entree_calc.group("sw"))
    
    basis_calc = re.search(r'Instellingsaandeel studentenen diplomawaarde basisberoepsopleidingen.*?(?P<basis>\d+(?:\.\d{3})*,\d{2}).*?(?P<cf>0,\d+).*?(?P<sw>\d+(?:\.\d{3})*,\d{2}).*?(?P<dw>\d+(?:\.\d{3})*,\d{2})', pdf_text, re.DOTALL)
    if basis_calc:
        data["basisberoeps"]["basis_studentenwaarde"] = parse_dutch_number(basis_calc.group("basis"))
        data["basisberoeps"]["correctiefactor"] = parse_dutch_number(basis_calc.group("cf"))
        data["basisberoeps"]["studentenwaarde"] = parse_dutch_number(basis_calc.group("sw"))
        data["basisberoeps"]["diplomawaarde"] = parse_dutch_number(basis_calc.group("dw"))
        data["basisberoeps"]["som"] = data["basisberoeps"]["studentenwaarde"] + data["basisberoeps"]["diplomawaarde"]
    
    vmks_calc = re.search(r'Instellingsaandeel studentenen diplomawaarde vak-.*?specialistenopleidingen.*?(?P<basis>\d+(?:\.\d{3})*,\d{2}).*?(?P<cf>0,\d+).*?(?P<sw>\d+(?:\.\d{3})*,\d{2}).*?(?P<dw>\d+(?:\.\d{3})*,\d{2})', pdf_text, re.DOTALL)
    if vmks_calc:
        data["vak_middenkader_specialisten"]["basis_studentenwaarde"] = parse_dutch_number(vmks_calc.group("basis"))
        data["vak_middenkader_specialisten"]["correctiefactor"] = parse_dutch_number(vmks_calc.group("cf"))
        data["vak_middenkader_specialisten"]["studentenwaarde"] = parse_dutch_number(vmks_calc.group("sw"))
        data["vak_middenkader_specialisten"]["diplomawaarde"] = parse_dutch_number(vmks_calc.group("dw"))
        data["vak_middenkader_specialisten"]["som"] = data["vak_middenkader_specialisten"]["studentenwaarde"] + data["vak_middenkader_specialisten"]["diplomawaarde"]
    
    # Extract student counts from total tables
    entree_stud = re.search(r'Totalen.*?(\d+).*?(\d+)\s*Basis voor instelling studentenwaarde', pdf_text, re.DOTALL)
    if entree_stud:
        data["entree"]["aantal_studenten_okt"] = int(entree_stud.group(1))
        data["entree"]["aantal_studenten_feb"] = int(entree_stud.group(2))
    
    # Extract totals from calculation pages
    basis_totals = re.search(r'Totalen:\s*(\d+(?:\.\d{3})*)\s*.*?(\d+(?:\.\d{3})*,\d{2})\s*(\d+)', pdf_text)
    if basis_totals:
        data["basisberoeps"]["aantal_studenten_okt"] = int(basis_totals.group(1).replace('.', ''))
        data["basisberoeps"]["aantal_studenten_feb"] = int(basis_totals.group(3))
    
    return data


def parse_dutch_number(s: str) -> float:
    """Parse Dutch number format (1.234,56 -> 1234.56)"""
    return float(s.replace('.', '').replace(',', '.'))


def extract_from_pdf_bytes(pdf_bytes: bytes, filename: str) -> dict:
    """Extract text from PDF using PyPDF2 or pdfplumber"""
    try:
        import pdfplumber
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            st.error("Installeer pdfplumber of PyPDF2: pip install pdfplumber")
            return None
    
    # Extract institution code from filename
    code_match = re.search(r'(\d{2}[A-Z]{2})', filename)
    inst_code = code_match.group(1) if code_match else "UNKN"
    
    data = extract_tbg_data(text, inst_code)
    data["raw_text"] = text[:2000]  # Store first 2000 chars for debugging
    return data


# ============================================================
# DEMO DATA (fallback when no PDF uploaded)
# ============================================================
DEMO_TWENTE = {
    "code": "27YU", "naam": "ROC van Twente", "datum": "10 maart 2026",
    "entree": {"studentenwaarde": 567.57, "instellingsaandeel_pct": 3.28069266, 
               "correctiefactor": 0.96689304, "aantal_studenten_okt": 642, "aantal_studenten_feb": 610},
    "basisberoeps": {"studentenwaarde": 1655.50, "diplomawaarde": 228.80, "som": 1884.30,
                    "instellingsaandeel_pct": 3.05854725, "correctiefactor": 0.99014778,
                    "aantal_studenten_okt": 2400, "aantal_studenten_feb": 2416, "diploma_niet_specialisten": 1144},
    "vak_middenkader_specialisten": {"studentenwaarde": 11320.70, "diplomawaarde": 2961.00, "som": 14281.70,
                                      "instellingsaandeel_pct": 3.77032828, "correctiefactor": 0.99048153,
                                      "aantal_studenten_okt": 14001, "aantal_studenten_feb": 13882, "diploma_niet_specialisten": 14607}
}

DEMO_GRAAFSCHAP = {
    "code": "24ZZ", "naam": "ROC Graafschap College", "datum": "18 november 2025",
    "entree": {"studentenwaarde": 168.50, "instellingsaandeel_pct": 1.03355274,
               "correctiefactor": 1.00000000, "aantal_studenten_okt": 198, "aantal_studenten_feb": 197},
    "basisberoeps": {"studentenwaarde": 1132.25, "diplomawaarde": 122.20, "som": 1254.45,
                    "instellingsaandeel_pct": 2.04577467, "correctiefactor": 0.99590164,
                    "aantal_studenten_okt": 1541, "aantal_studenten_feb": 1577, "diploma_niet_specialisten": 611},
    "vak_middenkader_specialisten": {"studentenwaarde": 4997.25, "diplomawaarde": 1398.60, "som": 6395.85,
                                      "instellingsaandeel_pct": 1.69355240, "correctiefactor": 0.99168383,
                                      "aantal_studenten_okt": 6250, "aantal_studenten_feb": 6231, "diploma_niet_specialisten": 6905}
}

LANDELIJK = {
    "entree": {"studentenwaarde": 17300.31},
    "basisberoeps": {"studentenwaarde": 55228.88, "diplomawaarde": 6378.80, "som": 61607.68},
    "vak_middenkader_specialisten": {"studentenwaarde": 301750.95, "diplomawaarde": 77041.00, "som": 378791.95}
}

# ============================================================
# VISUALIZATION FUNCTIONS
# ============================================================
def plot_instellingsaandelen(inst1, inst2):
    """Bar chart comparing institution shares"""
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    
    fig.add_trace(go.Bar(
        name=inst1['naam'], x=niveaus,
        y=[inst1['entree']['instellingsaandeel_pct'],
           inst1['basisberoeps']['instellingsaandeel_pct'],
           inst1['vak_middenkader_specialisten']['instellingsaandeel_pct']],
        marker_color='#2E86AB', textposition='outside',
        text=[f"{v:.2f}%" for v in [inst1['entree']['instellingsaandeel_pct'],
                                     inst1['basisberoeps']['instellingsaandeel_pct'],
                                     inst1['vak_middenkader_specialisten']['instellingsaandeel_pct']]]
    ))
    fig.add_trace(go.Bar(
        name=inst2['naam'], x=niveaus,
        y=[inst2['entree']['instellingsaandeel_pct'],
           inst2['basisberoeps']['instellingsaandeel_pct'],
           inst2['vak_middenkader_specialisten']['instellingsaandeel_pct']],
        marker_color='#A23B72', textposition='outside',
        text=[f"{v:.2f}%" for v in [inst2['entree']['instellingsaandeel_pct'],
                                     inst2['basisberoeps']['instellingsaandeel_pct'],
                                     inst2['vak_middenkader_specialisten']['instellingsaandeel_pct']]]
    ))
    
    fig.update_layout(
        barmode='group', title='Instellingsaandelen Vergelijking',
        yaxis_title='Instellingsaandeel (%)', template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=450
    )
    return fig


def plot_waarden_vergelijking(inst1, inst2):
    """Stacked bar chart student value + diploma value"""
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    
    # Student values
    fig.add_trace(go.Bar(name=f'Studentenwaarde ({inst1["naam"]})', x=niveaus,
        y=[inst1['entree']['studentenwaarde'], inst1['basisberoeps']['studentenwaarde'], inst1['vak_middenkader_specialisten']['studentenwaarde']],
        marker_color='#2E86AB'))
    fig.add_trace(go.Bar(name=f'Diplomawaarde ({inst1["naam"]})', x=niveaus,
        y=[0, inst1['basisberoeps']['diplomawaarde'], inst1['vak_middenkader_specialisten']['diplomawaarde']],
        marker_color='#1B4965'))
    
    fig.add_trace(go.Bar(name=f'Studentenwaarde ({inst2["naam"]})', x=niveaus,
        y=[inst2['entree']['studentenwaarde'], inst2['basisberoeps']['studentenwaarde'], inst2['vak_middenkader_specialisten']['studentenwaarde']],
        marker_color='#A23B72'))
    fig.add_trace(go.Bar(name=f'Diplomawaarde ({inst2["naam"]})', x=niveaus,
        y=[0, inst2['basisberoeps']['diplomawaarde'], inst2['vak_middenkader_specialisten']['diplomawaarde']],
        marker_color='#6A1B4D'))
    
    fig.update_layout(
        barmode='group', title='Studentenwaarde en Diplomawaarde',
        yaxis_title='Waarde', template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=500
    )
    return fig


def plot_mutatie(inst1, inst2):
    """Waterfall-style mutation chart"""
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    
    t_mut = [inst1['entree']['aantal_studenten_feb'] - inst1['entree']['aantal_studenten_okt'],
             inst1['basisberoeps']['aantal_studenten_feb'] - inst1['basisberoeps']['aantal_studenten_okt'],
             inst1['vak_middenkader_specialisten']['aantal_studenten_feb'] - inst1['vak_middenkader_specialisten']['aantal_studenten_okt']]
    g_mut = [inst2['entree']['aantal_studenten_feb'] - inst2['entree']['aantal_studenten_okt'],
             inst2['basisberoeps']['aantal_studenten_feb'] - inst2['basisberoeps']['aantal_studenten_okt'],
             inst2['vak_middenkader_specialisten']['aantal_studenten_feb'] - inst2['vak_middenkader_specialisten']['aantal_studenten_okt']]
    
    colors_t = ['#27AE60' if v >= 0 else '#E74C3C' for v in t_mut]
    colors_g = ['#27AE60' if v >= 0 else '#E74C3C' for v in g_mut]
    
    fig.add_trace(go.Bar(name=inst1['naam'], x=niveaus, y=t_mut, marker_color=colors_t,
                         text=[f"{v:+d}" for v in t_mut], textposition='outside'))
    fig.add_trace(go.Bar(name=inst2['naam'], x=niveaus, y=g_mut, marker_color=colors_g,
                         text=[f"{v:+d}" for v in g_mut], textposition='outside'))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        barmode='group', title='Studentenaantal Mutatie (okt 2025 → feb 2026)',
        yaxis_title='Mutatie', template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=450
    )
    return fig


def plot_correctiefactoren(inst1, inst2):
    """Correction factors comparison"""
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    
    fig.add_trace(go.Bar(name=inst1['naam'], x=niveaus,
        y=[inst1['entree']['correctiefactor'], inst1['basisberoeps']['correctiefactor'], inst1['vak_middenkader_specialisten']['correctiefactor']],
        marker_color='#2E86AB', text=[f"{v:.5f}" for v in [inst1['entree']['correctiefactor'], inst1['basisberoeps']['correctiefactor'], inst1['vak_middenkader_specialisten']['correctiefactor']]],
        textposition='outside'))
    fig.add_trace(go.Bar(name=inst2['naam'], x=niveaus,
        y=[inst2['entree']['correctiefactor'], inst2['basisberoeps']['correctiefactor'], inst2['vak_middenkader_specialisten']['correctiefactor']],
        marker_color='#A23B72', text=[f"{v:.5f}" for v in [inst2['entree']['correctiefactor'], inst2['basisberoeps']['correctiefactor'], inst2['vak_middenkader_specialisten']['correctiefactor']]],
        textposition='outside'))
    
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Referentie (1.0)")
    fig.update_layout(
        barmode='group', title='Correctiefactoren Vergelijking',
        yaxis_title='Correctiefactor', template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=450, yaxis=dict(range=[0.94, 1.02])
    )
    return fig


def plot_radar(inst1, inst2):
    """Radar chart with normalized metrics"""
    categories = ['Entree IA', 'Basis IA', 'VMK/S IA', 'Totaal SW', 'Totaal DW', 'Diploma-ratio', 'Studenten', 'CF gem']
    
    t_sw = inst1['entree']['studentenwaarde'] + inst1['basisberoeps']['studentenwaarde'] + inst1['vak_middenkader_specialisten']['studentenwaarde']
    g_sw = inst2['entree']['studentenwaarde'] + inst2['basisberoeps']['studentenwaarde'] + inst2['vak_middenkader_specialisten']['studentenwaarde']
    t_dw = inst1['basisberoeps']['diplomawaarde'] + inst1['vak_middenkader_specialisten']['diplomawaarde']
    g_dw = inst2['basisberoeps']['diplomawaarde'] + inst2['vak_middenkader_specialisten']['diplomawaarde']
    t_stud = inst1['entree']['aantal_studenten_feb'] + inst1['basisberoeps']['aantal_studenten_feb'] + inst1['vak_middenkader_specialisten']['aantal_studenten_feb']
    g_stud = inst2['entree']['aantal_studenten_feb'] + inst2['basisberoeps']['aantal_studenten_feb'] + inst2['vak_middenkader_specialisten']['aantal_studenten_feb']
    
    t_vals = [
        inst1['entree']['instellingsaandeel_pct']/4,
        inst1['basisberoeps']['instellingsaandeel_pct']/4,
        inst1['vak_middenkader_specialisten']['instellingsaandeel_pct']/4,
        t_sw/20000,
        t_dw/4000,
        (inst1['vak_middenkader_specialisten']['diplomawaarde']/inst1['vak_middenkader_specialisten']['studentenwaarde'])/0.3,
        t_stud/20000,
        np.mean([inst1['entree']['correctiefactor'], inst1['basisberoeps']['correctiefactor'], inst1['vak_middenkader_specialisten']['correctiefactor']])
    ]
    g_vals = [
        inst2['entree']['instellingsaandeel_pct']/4,
        inst2['basisberoeps']['instellingsaandeel_pct']/4,
        inst2['vak_middenkader_specialisten']['instellingsaandeel_pct']/4,
        g_sw/20000,
        g_dw/4000,
        (inst2['vak_middenkader_specialisten']['diplomawaarde']/inst2['vak_middenkader_specialisten']['studentenwaarde'])/0.3,
        g_stud/20000,
        np.mean([inst2['entree']['correctiefactor'], inst2['basisberoeps']['correctiefactor'], inst2['vak_middenkader_specialisten']['correctiefactor']])
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=t_vals + [t_vals[0]], theta=categories + [categories[0]],
        fill='toself', name=inst1['naam'], line_color='#2E86AB', fillcolor='rgba(46,134,171,0.2)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=g_vals + [g_vals[0]], theta=categories + [categories[0]],
        fill='toself', name=inst2['naam'], line_color='#A23B72', fillcolor='rgba(162,59,114,0.2)'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1.1])),
        showlegend=True, title='Vergelijkend Profiel (genormaliseerd)',
        template='plotly_white', height=550
    )
    return fig


def plot_landelijke_ranglijst(inst1, inst2):
    """Horizontal bar chart with national ranking context"""
    # Extended data from both PDFs
    instellingen = [
        ("ROC van Amsterdam", 25.61, 6.76), ("Firda", 16.41, 4.33),
        ("ROC van Twente", 14.28, 3.77), ("ROC Mondriaan", 14.19, 3.75),
        ("Zadkine", 13.95, 3.68), ("Summa College", 13.62, 3.60),
        ("Deltion College", 13.56, 3.58), ("ROC Midden Nederland", 13.36, 3.53),
        ("Talland College", 11.57, 3.05), ("Curio", 10.73, 2.83),
        ("Noorderpoort", 10.36, 2.74), ("Alfa-college", 8.20, 2.17),
        ("Yuverta", 7.62, 2.01), ("ROC Graafschap College", 6.44, 1.70)
    ]
    instellingen.sort(key=lambda x: x[1], reverse=True)
    
    colors = ['#2E86AB' if x[0] == inst1['naam'] else '#A23B72' if x[0] == inst2['naam'] else '#BDC3C7' 
              for x in instellingen]
    
    fig = go.Figure(go.Bar(
        y=[x[0] for x in instellingen],
        x=[x[1] for x in instellingen],
        orientation='h',
        marker_color=colors,
        text=[f"{x[1]:.0f}" for x in instellingen],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Vak-/Middenkader-/Specialisten: Landelijke Ranglijst',
        xaxis_title='Som studenten- en diplomawaarde (x1000)',
        template='plotly_white', height=500,
        yaxis=dict(autorange="reversed")
    )
    return fig


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/pdf-2.png", width=60)
    st.markdown("## 📁 Data Upload")
    st.markdown("Upload TBG PDF's om automatisch data te extraheren.")
    
    uploaded_files = st.file_uploader(
        "Upload TBG PDF's (max 2)", 
        type=['pdf'], 
        accept_multiple_files=True
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Instellingen")
    show_demo = st.checkbox("Gebruik demo-data als fallback", value=True)
    
    st.markdown("---")
    st.markdown("**ℹ️ Vereisten**")
    st.code("pip install streamlit plotly pdfplumber pandas", language="bash")
    
    st.markdown("**📄 Run app**")
    st.code("streamlit run app.py", language="bash")

# ============================================================
# MAIN APP
# ============================================================
st.markdown('<div class="main-header">📊 MBO Bekostigingsdashboard 2025/2026</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Vergelijkende analyse van Terugmelding Bekostigingsgrondslagen (TBG)</div>', unsafe_allow_html=True)

# Determine data source
inst1, inst2 = None, None

if uploaded_files and len(uploaded_files) >= 1:
    # Extract from uploaded PDFs
    extracted = []
    for f in uploaded_files[:2]:
        data = extract_from_pdf_bytes(f.getvalue(), f.name)
        if data:
            extracted.append(data)
    
    if len(extracted) >= 2:
        inst1, inst2 = extracted[0], extracted[1]
        st.success(f"✅ Data geëxtraheerd uit {len(extracted)} PDF's")
    elif len(extracted) == 1:
        inst1 = extracted[0]
        inst2 = DEMO_GRAAFSCHAP if inst1['code'] == '27YU' else DEMO_TWENTE
        st.info("ℹ️ Eén PDF geüpload, tweede instelling uit demo-data")
    elif show_demo:
        inst1, inst2 = DEMO_TWENTE, DEMO_GRAAFSCHAP
        st.info("ℹ️ Geen PDF's herkend, demo-data gebruikt")
else:
    if show_demo:
        inst1, inst2 = DEMO_TWENTE, DEMO_GRAAFSCHAP
        st.info("ℹ️ Demo-data actief. Upload PDF's voor eigen analyse.")

# Ensure we have data
if inst1 is None or inst2 is None:
    st.error("Geen data beschikbaar. Upload PDF's of schakel demo-data in.")
    st.stop()

# ============================================================
# KPI CARDS
# ============================================================
col1, col2, col3 = st.columns(3)

t_totaal = inst1['entree']['studentenwaarde'] + inst1['basisberoeps']['som'] + inst1['vak_middenkader_specialisten']['som']
g_totaal = inst2['entree']['studentenwaarde'] + inst2['basisberoeps']['som'] + inst2['vak_middenkader_specialisten']['som']
factor = t_totaal / g_totaal

with col1:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #2E86AB;">
        <div class="metric-label">{inst1['naam']}</div>
        <div class="metric-value">{t_totaal:,.0f}</div>
        <div class="metric-sub">Totale bekostigingswaarde</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #A23B72;">
        <div class="metric-label">{inst2['naam']}</div>
        <div class="metric-value">{g_totaal:,.0f}</div>
        <div class="metric-sub">Totale bekostigingswaarde</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #F59E0B;">
        <div class="metric-label">Verschil (factor)</div>
        <div class="metric-value">{factor:.2f}x</div>
        <div class="metric-sub">{inst1['naam']} is groter</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overzicht", "📊 Grafieken", "🎯 Profiel", "🏆 Ranglijst", "📋 Detailtabel"
])

with tab1:
    st.markdown("### Kernbevindingen")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="insight-box">
            <h4>📏 Schaalvergelijking</h4>
            <p><strong>{inst1['naam']}</strong> is <strong>{factor:.1f}x</strong> groter dan {inst2['naam']} op totale bekostigingswaarde.<br><br>
            • Studenten (feb): {inst1['entree']['aantal_studenten_feb']+inst1['basisberoeps']['aantal_studenten_feb']+inst1['vak_middenkader_specialisten']['aantal_studenten_feb']:,} vs {inst2['entree']['aantal_studenten_feb']+inst2['basisberoeps']['aantal_studenten_feb']+inst2['vak_middenkader_specialisten']['aantal_studenten_feb']:,}<br>
            • VMK/S waarde: {inst1['vak_middenkader_specialisten']['som']:,.0f} vs {inst2['vak_middenkader_specialisten']['som']:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_b:
        t_ratio = inst1['vak_middenkader_specialisten']['diplomawaarde'] / inst1['vak_middenkader_specialisten']['studentenwaarde']
        g_ratio = inst2['vak_middenkader_specialisten']['diplomawaarde'] / inst2['vak_middenkader_specialisten']['studentenwaarde']
        st.markdown(f"""
        <div class="insight-box">
            <h4>🎓 Diploma-output</h4>
            <p><strong>Diploma-ratio VMK/S:</strong><br>
            • {inst1['naam']}: {t_ratio:.3f}<br>
            • {inst2['naam']}: {g_ratio:.3f}<br><br>
            {'<strong>' + inst2['naam'] + '</strong> scoort relatief hoger op diploma-output.' if g_ratio > t_ratio else '<strong>' + inst1['naam'] + '</strong> scoort relatief hoger op diploma-output.'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Mini charts
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_instellingsaandelen(inst1, inst2), use_container_width=True)
    with c2:
        st.plotly_chart(plot_mutatie(inst1, inst2), use_container_width=True)

with tab2:
    metric = st.radio("Selecteer metric:", 
        ["Instellingsaandeel (%)", "Totale waarde", "Studentenaantal", "Mutatie okt→feb", "Correctiefactor"],
        horizontal=True)
    
    if metric == "Instellingsaandeel (%)":
        st.plotly_chart(plot_instellingsaandelen(inst1, inst2), use_container_width=True)
    elif metric == "Totale waarde":
        st.plotly_chart(plot_waarden_vergelijking(inst1, inst2), use_container_width=True)
    elif metric == "Studentenaantal":
        fig = go.Figure()
        niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
        fig.add_trace(go.Bar(name=inst1['naam'], x=niveaus,
            y=[inst1['entree']['aantal_studenten_feb'], inst1['basisberoeps']['aantal_studenten_feb'], inst1['vak_middenkader_specialisten']['aantal_studenten_feb']],
            marker_color='#2E86AB'))
        fig.add_trace(go.Bar(name=inst2['naam'], x=niveaus,
            y=[inst2['entree']['aantal_studenten_feb'], inst2['basisberoeps']['aantal_studenten_feb'], inst2['vak_middenkader_specialisten']['aantal_studenten_feb']],
            marker_color='#A23B72'))
        fig.update_layout(barmode='group', title='Studentenaantal (feb 2026)', template='plotly_white', height=500)
        st.plotly_chart(fig, use_container_width=True)
    elif metric == "Mutatie okt→feb":
        st.plotly_chart(plot_mutatie(inst1, inst2), use_container_width=True)
    else:
        st.plotly_chart(plot_correctiefactoren(inst1, inst2), use_container_width=True)

with tab3:
    col_r1, col_r2 = st.columns([3, 2])
    with col_r1:
        st.plotly_chart(plot_radar(inst1, inst2), use_container_width=True)
    with col_r2:
        st.markdown("""
        <div style="background:white;border-radius:12px;padding:1.5rem;border:1px solid #e5e7eb;">
            <h4 style="margin-top:0;color:#1e3a5f;">🎯 Profielinterpretatie</h4>
            <p style="font-size:0.9rem;color:#4b5563;line-height:1.6;">
            De radar toont genormaliseerde metrics (0-100%).<br><br>
            <strong style="color:#2E86AB;">Blauw:</strong> grotere schaal, hoger landelijk marktaandeel<br>
            <strong style="color:#A23B72;">Paars:</strong> compacter profiel, relatief hogere diploma-ratio
            </p>
        </div>
        """, unsafe_allow_html=True)

with tab4:
    st.plotly_chart(plot_landelijke_ranglijst(inst1, inst2), use_container_width=True)
    st.caption("Landelijke ranglijst gebaseerd op vak-/middenkader-/specialistenopleidingen. Data uit TBG 2025/2026.")

with tab5:
    # Create detailed comparison table
    df = pd.DataFrame({
        'Metric': ['Studentenwaarde', 'Diplomawaarde', 'Som (SW+DW)', 'Instellingsaandeel (%)', 
                   'Correctiefactor', 'Studenten okt 2025', 'Studenten feb 2026', 'Mutatie'],
        f'{inst1["naam"]} - Entree': [
            inst1['entree']['studentenwaarde'], '-', inst1['entree']['studentenwaarde'],
            inst1['entree']['instellingsaandeel_pct'], inst1['entree']['correctiefactor'],
            inst1['entree']['aantal_studenten_okt'], inst1['entree']['aantal_studenten_feb'],
            inst1['entree']['aantal_studenten_feb'] - inst1['entree']['aantal_studenten_okt']
        ],
        f'{inst2["naam"]} - Entree': [
            inst2['entree']['studentenwaarde'], '-', inst2['entree']['studentenwaarde'],
            inst2['entree']['instellingsaandeel_pct'], inst2['entree']['correctiefactor'],
            inst2['entree']['aantal_studenten_okt'], inst2['entree']['aantal_studenten_feb'],
            inst2['entree']['aantal_studenten_feb'] - inst2['entree']['aantal_studenten_okt']
        ],
        f'{inst1["naam"]} - Basis': [
            inst1['basisberoeps']['studentenwaarde'], inst1['basisberoeps']['diplomawaarde'], inst1['basisberoeps']['som'],
            inst1['basisberoeps']['instellingsaandeel_pct'], inst1['basisberoeps']['correctiefactor'],
            inst1['basisberoeps']['aantal_studenten_okt'], inst1['basisberoeps']['aantal_studenten_feb'],
            inst1['basisberoeps']['aantal_studenten_feb'] - inst1['basisberoeps']['aantal_studenten_okt']
        ],
        f'{inst2["naam"]} - Basis': [
            inst2['basisberoeps']['studentenwaarde'], inst2['basisberoeps']['diplomawaarde'], inst2['basisberoeps']['som'],
            inst2['basisberoeps']['instellingsaandeel_pct'], inst2['basisberoeps']['correctiefactor'],
            inst2['basisberoeps']['aantal_studenten_okt'], inst2['basisberoeps']['aantal_studenten_feb'],
            inst2['basisberoeps']['aantal_studenten_feb'] - inst2['basisberoeps']['aantal_studenten_okt']
        ],
        f'{inst1["naam"]} - VMK/S': [
            inst1['vak_middenkader_specialisten']['studentenwaarde'], inst1['vak_middenkader_specialisten']['diplomawaarde'], inst1['vak_middenkader_specialisten']['som'],
            inst1['vak_middenkader_specialisten']['instellingsaandeel_pct'], inst1['vak_middenkader_specialisten']['correctiefactor'],
            inst1['vak_middenkader_specialisten']['aantal_studenten_okt'], inst1['vak_middenkader_specialisten']['aantal_studenten_feb'],
            inst1['vak_middenkader_specialisten']['aantal_studenten_feb'] - inst1['vak_middenkader_specialisten']['aantal_studenten_okt']
        ],
        f'{inst2["naam"]} - VMK/S': [
            inst2['vak_middenkader_specialisten']['studentenwaarde'], inst2['vak_middenkader_specialisten']['diplomawaarde'], inst2['vak_middenkader_specialisten']['som'],
            inst2['vak_middenkader_specialisten']['instellingsaandeel_pct'], inst2['vak_middenkader_specialisten']['correctiefactor'],
            inst2['vak_middenkader_specialisten']['aantal_studenten_okt'], inst2['vak_middenkader_specialisten']['aantal_studenten_feb'],
            inst2['vak_middenkader_specialisten']['aantal_studenten_feb'] - inst2['vak_middenkader_specialisten']['aantal_studenten_okt']
        ]
    })
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download als CSV", csv, "tbg_vergelijking.csv", "text/csv")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("MBO Bekostigingsdashboard | Data: DUO TBG 2025/2026 | Gegenereerd met Streamlit & Plotly")
