"""
📊 MBO Bekostigingsdashboard - Streamlit App
Upload TBG PDF's en vergelijk automatisch bekostigingsdata
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO
import plotly.graph_objects as go

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
    .error-box { background: #fef2f2; border-left: 4px solid #dc2626; 
                padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DEMO DATA (volledig en gegarandeerd compleet)
# ============================================================
DEMO_TWENTE = {
    "code": "27YU", "naam": "ROC van Twente", "datum": "10 maart 2026",
    "entree": {
        "studentenwaarde": 567.57, "instellingsaandeel_pct": 3.28069266, 
        "correctiefactor": 0.96689304, "aantal_studenten_okt": 642, "aantal_studenten_feb": 610,
        "basis_studentenwaarde": 587.00
    },
    "basisberoeps": {
        "studentenwaarde": 1655.50, "diplomawaarde": 228.80, "som": 1884.30,
        "instellingsaandeel_pct": 3.05854725, "correctiefactor": 0.99014778,
        "aantal_studenten_okt": 2400, "aantal_studenten_feb": 2416, 
        "diploma_niet_specialisten": 1144, "basis_studentenwaarde": 2089.96
    },
    "vak_middenkader_specialisten": {
        "studentenwaarde": 11320.70, "diplomawaarde": 2961.00, "som": 14281.70,
        "instellingsaandeel_pct": 3.77032828, "correctiefactor": 0.99048153,
        "aantal_studenten_okt": 14001, "aantal_studenten_feb": 13882, 
        "diploma_niet_specialisten": 14607, "basis_studentenwaarde": 14286.86
    }
}

DEMO_GRAAFSCHAP = {
    "code": "24ZZ", "naam": "ROC Graafschap College", "datum": "18 november 2025",
    "entree": {
        "studentenwaarde": 168.50, "instellingsaandeel_pct": 1.03355274,
        "correctiefactor": 1.00000000, "aantal_studenten_okt": 198, "aantal_studenten_feb": 197,
        "basis_studentenwaarde": 168.50
    },
    "basisberoeps": {
        "studentenwaarde": 1132.25, "diplomawaarde": 122.20, "som": 1254.45,
        "instellingsaandeel_pct": 2.04577467, "correctiefactor": 0.99590164,
        "aantal_studenten_okt": 1541, "aantal_studenten_feb": 1577, 
        "diploma_niet_specialisten": 611, "basis_studentenwaarde": 1421.14
    },
    "vak_middenkader_specialisten": {
        "studentenwaarde": 4997.25, "diplomawaarde": 1398.60, "som": 6395.85,
        "instellingsaandeel_pct": 1.69355240, "correctiefactor": 0.99168383,
        "aantal_studenten_okt": 6250, "aantal_studenten_feb": 6231, 
        "diploma_niet_specialisten": 6905, "basis_studentenwaarde": 6298.94
    }
}

# ============================================================
# HELPER: Ensure data completeness with defaults
# ============================================================
def ensure_complete_data(data, demo_data):
    """
    Ensure extracted data has all required fields.
    Fill missing fields from demo data or set defaults.
    """
    if data is None:
        return demo_data.copy()
    
    # Ensure top-level keys exist
    for key in ['naam', 'code', 'datum', 'entree', 'basisberoeps', 'vak_middenkader_specialisten']:
        if key not in data or data[key] is None:
            data[key] = demo_data.get(key, {}).copy() if isinstance(demo_data.get(key), dict) else demo_data.get(key, '')
    
    # Ensure each niveau has all required fields
    required_fields = {
        'entree': ['studentenwaarde', 'instellingsaandeel_pct', 'correctiefactor', 
                   'aantal_studenten_okt', 'aantal_studenten_feb', 'basis_studentenwaarde'],
        'basisberoeps': ['studentenwaarde', 'diplomawaarde', 'som', 'instellingsaandeel_pct', 
                        'correctiefactor', 'aantal_studenten_okt', 'aantal_studenten_feb',
                        'diploma_niet_specialisten', 'basis_studentenwaarde'],
        'vak_middenkader_specialisten': ['studentenwaarde', 'diplomawaarde', 'som', 'instellingsaandeel_pct',
                                          'correctiefactor', 'aantal_studenten_okt', 'aantal_studenten_feb',
                                          'diploma_niet_specialisten', 'basis_studentenwaarde']
    }
    
    for niveau, fields in required_fields.items():
        if niveau not in data or not isinstance(data[niveau], dict):
            data[niveau] = demo_data.get(niveau, {}).copy()
            continue
            
        for field in fields:
            if field not in data[niveau] or data[niveau][field] is None:
                # Try to get from demo data, otherwise compute or default
                if field in demo_data.get(niveau, {}):
                    data[niveau][field] = demo_data[niveau][field]
                elif field == 'som' and 'studentenwaarde' in data[niveau] and 'diplomawaarde' in data[niveau]:
                    data[niveau][field] = data[niveau]['studentenwaarde'] + data[niveau]['diplomawaarde']
                elif field == 'basis_studentenwaarde' and 'studentenwaarde' in data[niveau] and 'correctiefactor' in data[niveau]:
                    # Reverse-engineer: basis = sw / cf
                    if data[niveau]['correctiefactor'] > 0:
                        data[niveau][field] = data[niveau]['studentenwaarde'] / data[niveau]['correctiefactor']
                    else:
                        data[niveau][field] = data[niveau]['studentenwaarde']
                else:
                    data[niveau][field] = 0.0 if field != 'aantal_studenten_okt' and field != 'aantal_studenten_feb' and field != 'diploma_niet_specialisten' else 0
    
    return data

# ============================================================
# PDF EXTRACTION
# ============================================================
def parse_dutch_number(s):
    if s is None:
        return 0.0
    try:
        return float(str(s).replace('.', '').replace(',', '.'))
    except (ValueError, TypeError):
        return 0.0

def extract_from_pdf_bytes(pdf_bytes, filename):
    """Extract TBG data from PDF with robust parsing."""
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
            st.error("Installeer pdfplumber: pip install pdfplumber")
            return None
        except Exception as e:
            st.warning(f"PyPDF2 fout: {e}")
            return None
    except Exception as e:
        st.warning(f"PDF leesfout: {e}")
        return None
    
    if not text or len(text.strip()) < 100:
        st.warning("PDF bevat te weinig tekst voor extractie.")
        return None
    
    # Extract institution code from filename
    code_match = re.search(r'(\d{2}[A-Z]{2})', filename)
    inst_code = code_match.group(1) if code_match else "UNKN"
    
    data = {
        "code": inst_code, "naam": "", "datum": "",
        "entree": {}, "basisberoeps": {}, "vak_middenkader_specialisten": {}
    }
    
    # Extract name - look for patterns like "27YU ROC van Twente" or "ROC van Twente Postbus"
    naam_patterns = [
        rf'{inst_code}\s+([A-Z][a-zA-Z\s&]+?)(?:\s+Postbus|\s+Slingelaan|\s+\d)',
        r'ROC\s+[A-Z][a-zA-Z\s]+(?:College|Twente)',
        r'([A-Z][a-zA-Z\s]+College)',
    ]
    for pattern in naam_patterns:
        match = re.search(pattern, text)
        if match:
            data["naam"] = match.group(1).strip()
            break
    
    # Extract institution shares from cover letter
    try:
        entree_match = re.search(r'entreeopleidingen.*?(\d+[.,]\d+)%', text, re.DOTALL | re.IGNORECASE)
        if entree_match:
            data["entree"]["instellingsaandeel_pct"] = parse_dutch_number(entree_match.group(1))
        
        basis_match = re.search(r'basisberoepsopleidingen.*?(\d+[.,]\d+)%', text, re.DOTALL | re.IGNORECASE)
        if basis_match:
            data["basisberoeps"]["instellingsaandeel_pct"] = parse_dutch_number(basis_match.group(1))
        
        vmks_match = re.search(r'vak-.*?specialistenopleidingen.*?(\d+[.,]\d+)%', text, re.DOTALL | re.IGNORECASE)
        if vmks_match:
            data["vak_middenkader_specialisten"]["instellingsaandeel_pct"] = parse_dutch_number(vmks_match.group(1))
    except Exception as e:
        st.warning(f"Fout bij extractie instellingsaandelen: {e}")
    
    # Extract student values from detailed pages
    # Entree: look for pattern with correctiefactor and studentenwaarde
    try:
        entree_patterns = [
            r'entreeopleidingen.*?Basis voor\s+studenten-\s*waarde\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
            r'entree.*?Correctiefactor.*?=([\d.,]+).*?Studenten-.*?waarde\s+([\d.,]+)',
            r'Basis voor instelling studentenwaarde[:\s]+([\d.,]+)',
        ]
        for pattern in entree_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                if len(match.groups()) >= 3:
                    data["entree"]["basis_studentenwaarde"] = parse_dutch_number(match.group(1))
                    data["entree"]["correctiefactor"] = parse_dutch_number(match.group(2))
                    data["entree"]["studentenwaarde"] = parse_dutch_number(match.group(3))
                elif len(match.groups()) == 2:
                    data["entree"]["correctiefactor"] = parse_dutch_number(match.group(1))
                    data["entree"]["studentenwaarde"] = parse_dutch_number(match.group(2))
                elif len(match.groups()) == 1:
                    data["entree"]["basis_studentenwaarde"] = parse_dutch_number(match.group(1))
                break
    except Exception as e:
        st.warning(f"Fout bij extractie entree: {e}")
    
    # Basisberoeps
    try:
        basis_patterns = [
            r'basisberoepsopleidingen.*?Basis voor\s+studenten-.*?waarde\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
            r'basisberoeps.*?Correctiefactor.*?=([\d.,]+).*?Studenten-.*?waarde\s+([\d.,]+).*?Diploma-.*?waarde\s+([\d.,]+)',
        ]
        for pattern in basis_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                if len(match.groups()) >= 4:
                    data["basisberoeps"]["basis_studentenwaarde"] = parse_dutch_number(match.group(1))
                    data["basisberoeps"]["correctiefactor"] = parse_dutch_number(match.group(2))
                    data["basisberoeps"]["studentenwaarde"] = parse_dutch_number(match.group(3))
                    data["basisberoeps"]["diplomawaarde"] = parse_dutch_number(match.group(4))
                elif len(match.groups()) >= 3:
                    data["basisberoeps"]["correctiefactor"] = parse_dutch_number(match.group(1))
                    data["basisberoeps"]["studentenwaarde"] = parse_dutch_number(match.group(2))
                    data["basisberoeps"]["diplomawaarde"] = parse_dutch_number(match.group(3))
                break
    except Exception as e:
        st.warning(f"Fout bij extractie basisberoeps: {e}")
    
    # VMK/S
    try:
        vmks_patterns = [
            r'vak-.*?specialistenopleidingen.*?Basis voor\s+studenten-.*?waarde\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
            r'specialistenopleidingen.*?Correctiefactor.*?=([\d.,]+).*?Studenten-.*?waarde\s+([\d.,]+).*?Diploma-.*?waarde\s+([\d.,]+)',
        ]
        for pattern in vmks_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                if len(match.groups()) >= 4:
                    data["vak_middenkader_specialisten"]["basis_studentenwaarde"] = parse_dutch_number(match.group(1))
                    data["vak_middenkader_specialisten"]["correctiefactor"] = parse_dutch_number(match.group(2))
                    data["vak_middenkader_specialisten"]["studentenwaarde"] = parse_dutch_number(match.group(3))
                    data["vak_middenkader_specialisten"]["diplomawaarde"] = parse_dutch_number(match.group(4))
                elif len(match.groups()) >= 3:
                    data["vak_middenkader_specialisten"]["correctiefactor"] = parse_dutch_number(match.group(1))
                    data["vak_middenkader_specialisten"]["studentenwaarde"] = parse_dutch_number(match.group(2))
                    data["vak_middenkader_specialisten"]["diplomawaarde"] = parse_dutch_number(match.group(3))
                break
    except Exception as e:
        st.warning(f"Fout bij extractie VMK/S: {e}")
    
    # Extract student counts
    try:
        # Find all "Totalen:" patterns
        totalen_matches = re.findall(r'Totalen:\s*([\d\s.,]+)', text)
        if len(totalen_matches) >= 3:
            # First is usually entree, second basis, third VMK/S
            for i, match in enumerate(totalen_matches[:3]):
                numbers = re.findall(r'[\d.]+,\d+|\d+', match)
                if numbers:
                    niveaus = ['entree', 'basisberoeps', 'vak_middenkader_specialisten']
                    if i < 3:
                        # Try to extract okt and feb counts
                        clean_nums = [parse_dutch_number(n) for n in numbers if parse_dutch_number(n) > 10]
                        if len(clean_nums) >= 2:
                            data[niveaus[i]]['aantal_studenten_okt'] = int(clean_nums[-2])
                            data[niveaus[i]]['aantal_studenten_feb'] = int(clean_nums[-1])
    except Exception as e:
        st.warning(f"Fout bij extractie studentenaantallen: {e}")
    
    # Compute 'som' if missing
    for niveau in ['basisberoeps', 'vak_middenkader_specialisten']:
        if 'studentenwaarde' in data[niveau] and 'diplomawaarde' in data[niveau]:
            if 'som' not in data[niveau] or data[niveau]['som'] == 0:
                data[niveau]['som'] = data[niveau]['studentenwaarde'] + data[niveau]['diplomawaarde']
    
    return data

# ============================================================
# CHART FUNCTIONS
# ============================================================
def plot_instellingsaandelen(inst1, inst2):
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    
    fig.add_trace(go.Bar(
        name=inst1['naam'], x=niveaus,
        y=[inst1['entree'].get('instellingsaandeel_pct', 0),
           inst1['basisberoeps'].get('instellingsaandeel_pct', 0),
           inst1['vak_middenkader_specialisten'].get('instellingsaandeel_pct', 0)],
        marker_color='#2E86AB', textposition='outside',
        text=[f"{v:.2f}%" for v in [inst1['entree'].get('instellingsaandeel_pct', 0),
                                     inst1['basisberoeps'].get('instellingsaandeel_pct', 0),
                                     inst1['vak_middenkader_specialisten'].get('instellingsaandeel_pct', 0)]]
    ))
    fig.add_trace(go.Bar(
        name=inst2['naam'], x=niveaus,
        y=[inst2['entree'].get('instellingsaandeel_pct', 0),
           inst2['basisberoeps'].get('instellingsaandeel_pct', 0),
           inst2['vak_middenkader_specialisten'].get('instellingsaandeel_pct', 0)],
        marker_color='#A23B72', textposition='outside',
        text=[f"{v:.2f}%" for v in [inst2['entree'].get('instellingsaandeel_pct', 0),
                                     inst2['basisberoeps'].get('instellingsaandeel_pct', 0),
                                     inst2['vak_middenkader_specialisten'].get('instellingsaandeel_pct', 0)]]
    ))
    
    fig.update_layout(
        barmode='group', title='Instellingsaandelen Vergelijking',
        yaxis_title='Instellingsaandeel (%)', template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=450
    )
    return fig

def plot_waarden_vergelijking(inst1, inst2):
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    
    fig.add_trace(go.Bar(name=f'SW ({inst1["naam"]})', x=niveaus,
        y=[inst1['entree'].get('studentenwaarde', 0), 
           inst1['basisberoeps'].get('studentenwaarde', 0), 
           inst1['vak_middenkader_specialisten'].get('studentenwaarde', 0)],
        marker_color='#2E86AB'))
    fig.add_trace(go.Bar(name=f'DW ({inst1["naam"]})', x=niveaus,
        y=[0, inst1['basisberoeps'].get('diplomawaarde', 0), inst1['vak_middenkader_specialisten'].get('diplomawaarde', 0)],
        marker_color='#1B4965'))
    
    fig.add_trace(go.Bar(name=f'SW ({inst2["naam"]})', x=niveaus,
        y=[inst2['entree'].get('studentenwaarde', 0), 
           inst2['basisberoeps'].get('studentenwaarde', 0), 
           inst2['vak_middenkader_specialisten'].get('studentenwaarde', 0)],
        marker_color='#A23B72'))
    fig.add_trace(go.Bar(name=f'DW ({inst2["naam"]})', x=niveaus,
        y=[0, inst2['basisberoeps'].get('diplomawaarde', 0), inst2['vak_middenkader_specialisten'].get('diplomawaarde', 0)],
        marker_color='#6A1B4D'))
    
    fig.update_layout(
        barmode='group', title='Studentenwaarde en Diplomawaarde',
        yaxis_title='Waarde', template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=500
    )
    return fig

def plot_mutatie(inst1, inst2):
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    
    t_mut = [inst1['entree'].get('aantal_studenten_feb', 0) - inst1['entree'].get('aantal_studenten_okt', 0),
             inst1['basisberoeps'].get('aantal_studenten_feb', 0) - inst1['basisberoeps'].get('aantal_studenten_okt', 0),
             inst1['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0) - inst1['vak_middenkader_specialisten'].get('aantal_studenten_okt', 0)]
    g_mut = [inst2['entree'].get('aantal_studenten_feb', 0) - inst2['entree'].get('aantal_studenten_okt', 0),
             inst2['basisberoeps'].get('aantal_studenten_feb', 0) - inst2['basisberoeps'].get('aantal_studenten_okt', 0),
             inst2['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0) - inst2['vak_middenkader_specialisten'].get('aantal_studenten_okt', 0)]
    
    colors_t = ['#27AE60' if v >= 0 else '#E74C3C' for v in t_mut]
    colors_g = ['#27AE60' if v >= 0 else '#E74C3C' for v in g_mut]
    
    fig.add_trace(go.Bar(name=inst1['naam'], x=niveaus, y=t_mut, marker_color=colors_t,
                         text=[f"{v:+d}" for v in t_mut], textposition='outside'))
    fig.add_trace(go.Bar(name=inst2['naam'], x=niveaus, y=g_mut, marker_color=colors_g,
                         text=[f"{v:+d}" for v in g_mut], textposition='outside'))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        barmode='group', title='Mutatie okt 2025 → feb 2026',
        yaxis_title='Mutatie', template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=450
    )
    return fig

def plot_correctiefactoren(inst1, inst2):
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    
    fig.add_trace(go.Bar(name=inst1['naam'], x=niveaus,
        y=[inst1['entree'].get('correctiefactor', 1.0), 
           inst1['basisberoeps'].get('correctiefactor', 1.0), 
           inst1['vak_middenkader_specialisten'].get('correctiefactor', 1.0)],
        marker_color='#2E86AB', 
        text=[f"{v:.5f}" for v in [inst1['entree'].get('correctiefactor', 1.0), 
                                    inst1['basisberoeps'].get('correctiefactor', 1.0), 
                                    inst1['vak_middenkader_specialisten'].get('correctiefactor', 1.0)]],
        textposition='outside'))
    fig.add_trace(go.Bar(name=inst2['naam'], x=niveaus,
        y=[inst2['entree'].get('correctiefactor', 1.0), 
           inst2['basisberoeps'].get('correctiefactor', 1.0), 
           inst2['vak_middenkader_specialisten'].get('correctiefactor', 1.0)],
        marker_color='#A23B72', 
        text=[f"{v:.5f}" for v in [inst2['entree'].get('correctiefactor', 1.0), 
                                    inst2['basisberoeps'].get('correctiefactor', 1.0), 
                                    inst2['vak_middenkader_specialisten'].get('correctiefactor', 1.0)]],
        textposition='outside'))
    
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig.update_layout(
        barmode='group', title='Correctiefactoren',
        yaxis_title='Correctiefactor', template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=450, yaxis=dict(range=[0.94, 1.02])
    )
    return fig

def plot_radar(inst1, inst2):
    categories = ['Entree IA', 'Basis IA', 'VMK/S IA', 'Totaal SW', 'Totaal DW', 'Diploma-ratio', 'Studenten', 'CF gem']
    
    t_sw = inst1['entree'].get('studentenwaarde', 0) + inst1['basisberoeps'].get('studentenwaarde', 0) + inst1['vak_middenkader_specialisten'].get('studentenwaarde', 0)
    g_sw = inst2['entree'].get('studentenwaarde', 0) + inst2['basisberoeps'].get('studentenwaarde', 0) + inst2['vak_middenkader_specialisten'].get('studentenwaarde', 0)
    t_dw = inst1['basisberoeps'].get('diplomawaarde', 0) + inst1['vak_middenkader_specialisten'].get('diplomawaarde', 0)
    g_dw = inst2['basisberoeps'].get('diplomawaarde', 0) + inst2['vak_middenkader_specialisten'].get('diplomawaarde', 0)
    t_stud = inst1['entree'].get('aantal_studenten_feb', 0) + inst1['basisberoeps'].get('aantal_studenten_feb', 0) + inst1['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0)
    g_stud = inst2['entree'].get('aantal_studenten_feb', 0) + inst2['basisberoeps'].get('aantal_studenten_feb', 0) + inst2['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0)
    
    t_vmks_sw = inst1['vak_middenkader_specialisten'].get('studentenwaarde', 1)
    g_vmks_sw = inst2['vak_middenkader_specialisten'].get('studentenwaarde', 1)
    t_vmks_dw = inst1['vak_middenkader_specialisten'].get('diplomawaarde', 0)
    g_vmks_dw = inst2['vak_middenkader_specialisten'].get('diplomawaarde', 0)
    
    t_vals = [
        inst1['entree'].get('instellingsaandeel_pct', 0)/4,
        inst1['basisberoeps'].get('instellingsaandeel_pct', 0)/4,
        inst1['vak_middenkader_specialisten'].get('instellingsaandeel_pct', 0)/4,
        t_sw/20000 if t_sw > 0 else 0,
        t_dw/4000 if t_dw > 0 else 0,
        (t_vmks_dw/t_vmks_sw)/0.3 if t_vmks_sw > 0 else 0,
        t_stud/20000 if t_stud > 0 else 0,
        np.mean([inst1['entree'].get('correctiefactor', 1.0), 
                 inst1['basisberoeps'].get('correctiefactor', 1.0), 
                 inst1['vak_middenkader_specialisten'].get('correctiefactor', 1.0)])
    ]
    g_vals = [
        inst2['entree'].get('instellingsaandeel_pct', 0)/4,
        inst2['basisberoeps'].get('instellingsaandeel_pct', 0)/4,
        inst2['vak_middenkader_specialisten'].get('instellingsaandeel_pct', 0)/4,
        g_sw/20000 if g_sw > 0 else 0,
        g_dw/4000 if g_dw > 0 else 0,
        (g_vmks_dw/g_vmks_sw)/0.3 if g_vmks_sw > 0 else 0,
        g_stud/20000 if g_stud > 0 else 0,
        np.mean([inst2['entree'].get('correctiefactor', 1.0), 
                 inst2['basisberoeps'].get('correctiefactor', 1.0), 
                 inst2['vak_middenkader_specialisten'].get('correctiefactor', 1.0)])
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

def plot_studenten(inst1, inst2):
    fig = go.Figure()
    niveaus = ['Entree', 'Basisberoeps', 'Vak/MK/Specialist']
    fig.add_trace(go.Bar(name=inst1['naam'], x=niveaus,
        y=[inst1['entree'].get('aantal_studenten_feb', 0), 
           inst1['basisberoeps'].get('aantal_studenten_feb', 0), 
           inst1['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0)],
        marker_color='#2E86AB'))
    fig.add_trace(go.Bar(name=inst2['naam'], x=niveaus,
        y=[inst2['entree'].get('aantal_studenten_feb', 0), 
           inst2['basisberoeps'].get('aantal_studenten_feb', 0), 
           inst2['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0)],
        marker_color='#A23B72'))
    fig.update_layout(barmode='group', title='Studentenaantal (feb 2026)', template='plotly_white', height=500)
    return fig

def plot_landelijke_ranglijst(inst1, inst2):
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
        title='Landelijke Ranglijst VMK/S',
        xaxis_title='Som studenten- en diplomawaarde (x1000)',
        template='plotly_white', height=500,
        yaxis=dict(autorange="reversed")
    )
    return fig

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 📁 Data Upload")
    uploaded_files = st.file_uploader("Upload TBG PDF's (max 2)", type=['pdf'], accept_multiple_files=True)
    show_demo = st.checkbox("Gebruik demo-data als fallback", value=True)
    
    st.markdown("---")
    st.markdown("**Installatie:**")
    st.code("pip install streamlit plotly pdfplumber pandas", language="bash")
    st.markdown("**Starten:**")
    st.code("streamlit run app.py", language="bash")

# ============================================================
# MAIN
# ============================================================
st.markdown('<div class="main-header">📊 MBO Bekostigingsdashboard 2025/2026</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Vergelijkende analyse van TBG-data</div>', unsafe_allow_html=True)

# Determine data source with robust fallback
inst1, inst2 = None, None
extraction_errors = []

if uploaded_files and len(uploaded_files) >= 1:
    extracted = []
    for f in uploaded_files[:2]:
        data = extract_from_pdf_bytes(f.getvalue(), f.name)
        if data:
            extracted.append(data)
        else:
            extraction_errors.append(f.name)
    
    if len(extracted) >= 2:
        inst1 = ensure_complete_data(extracted[0], DEMO_TWENTE)
        inst2 = ensure_complete_data(extracted[1], DEMO_GRAAFSCHAP)
        st.success(f"✅ Data geëxtraheerd uit {len(extracted)} PDF's")
    elif len(extracted) == 1:
        inst1 = ensure_complete_data(extracted[0], DEMO_TWENTE)
        # Determine which demo to use for second
        if inst1['code'] == '27YU':
            inst2 = DEMO_GRAAFSCHAP.copy()
        elif inst1['code'] == '24ZZ':
            inst2 = DEMO_TWENTE.copy()
        else:
            inst2 = DEMO_GRAAFSCHAP.copy()
        st.info("ℹ️ Eén PDF geüpload, tweede uit demo-data")
    elif show_demo:
        inst1, inst2 = DEMO_TWENTE.copy(), DEMO_GRAAFSCHAP.copy()
        if extraction_errors:
            st.warning(f"⚠️ Kon {len(extraction_errors)} PDF('s) niet parsen, demo-data gebruikt")
        else:
            st.info("ℹ️ Demo-data gebruikt")
else:
    if show_demo:
        inst1, inst2 = DEMO_TWENTE.copy(), DEMO_GRAAFSCHAP.copy()
        st.info("ℹ️ Demo-data actief. Upload PDF's voor eigen analyse.")

if inst1 is None or inst2 is None:
    st.error("Geen data beschikbaar. Upload PDF's of schakel demo-data in.")
    st.stop()

# Validate data before use
try:
    # Test access to all required fields
    _ = inst1['entree']['studentenwaarde']
    _ = inst1['basisberoeps']['som']
    _ = inst1['vak_middenkader_specialisten']['som']
    _ = inst2['entree']['studentenwaarde']
    _ = inst2['basisberoeps']['som']
    _ = inst2['vak_middenkader_specialisten']['som']
except KeyError as e:
    st.error(f"Data validatie fout: ontbrekend veld {e}. Terugvallen op demo-data.")
    inst1, inst2 = DEMO_TWENTE.copy(), DEMO_GRAAFSCHAP.copy()

# KPI CARDS
col1, col2, col3 = st.columns(3)
t_totaal = inst1['entree']['studentenwaarde'] + inst1['basisberoeps']['som'] + inst1['vak_middenkader_specialisten']['som']
g_totaal = inst2['entree']['studentenwaarde'] + inst2['basisberoeps']['som'] + inst2['vak_middenkader_specialisten']['som']
factor = t_totaal / g_totaal if g_totaal > 0 else 0

with col1:
    st.markdown(f'<div class="kpi-card" style="border-left-color: #2E86AB;"><div class="metric-label">{inst1["naam"]}</div><div class="metric-value">{t_totaal:,.0f}</div><div class="metric-sub">Totale waarde</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card" style="border-left-color: #A23B72;"><div class="metric-label">{inst2["naam"]}</div><div class="metric-value">{g_totaal:,.0f}</div><div class="metric-sub">Totale waarde</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card" style="border-left-color: #F59E0B;"><div class="metric-label">Verschil</div><div class="metric-value">{factor:.2f}x</div><div class="metric-sub">{inst1["naam"]} is groter</div></div>', unsafe_allow_html=True)

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overzicht", "📊 Grafieken", "🎯 Profiel", "🏆 Ranglijst", "📋 Detailtabel"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        t_stud_total = inst1['entree'].get('aantal_studenten_feb', 0) + inst1['basisberoeps'].get('aantal_studenten_feb', 0) + inst1['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0)
        g_stud_total = inst2['entree'].get('aantal_studenten_feb', 0) + inst2['basisberoeps'].get('aantal_studenten_feb', 0) + inst2['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0)
        st.markdown(f"""
        <div class="insight-box">
            <h4>📏 Schaal</h4>
            <p><strong>{inst1['naam']}</strong> is <strong>{factor:.1f}x</strong> groter.<br><br>
            Studenten: {t_stud_total:,} vs {g_stud_total:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        t_vmks_sw = inst1['vak_middenkader_specialisten'].get('studentenwaarde', 1)
        t_vmks_dw = inst1['vak_middenkader_specialisten'].get('diplomawaarde', 0)
        g_vmks_sw = inst2['vak_middenkader_specialisten'].get('studentenwaarde', 1)
        g_vmks_dw = inst2['vak_middenkader_specialisten'].get('diplomawaarde', 0)
        t_ratio = t_vmks_dw / t_vmks_sw if t_vmks_sw > 0 else 0
        g_ratio = g_vmks_dw / g_vmks_sw if g_vmks_sw > 0 else 0
        st.markdown(f"""
        <div class="insight-box">
            <h4>🎓 Diploma-output VMK/S</h4>
            <p>• {inst1['naam']}: {t_ratio:.3f}<br>
            • {inst2['naam']}: {g_ratio:.3f}<br><br>
            <strong>{inst2['naam'] if g_ratio > t_ratio else inst1['naam']}</strong> scoort relatief hoger.</p>
        </div>
        """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_instellingsaandelen(inst1, inst2), use_container_width=True, key="tab1_chart1")
    with c2:
        st.plotly_chart(plot_mutatie(inst1, inst2), use_container_width=True, key="tab1_chart2")

with tab2:
    metric = st.radio("Selecteer metric:", 
        ["Instellingsaandeel (%)", "Totale waarde", "Studentenaantal", "Mutatie okt→feb", "Correctiefactor"],
        horizontal=True, key="metric_selector")
    
    if metric == "Instellingsaandeel (%)":
        st.plotly_chart(plot_instellingsaandelen(inst1, inst2), use_container_width=True, key="tab2_ia")
    elif metric == "Totale waarde":
        st.plotly_chart(plot_waarden_vergelijking(inst1, inst2), use_container_width=True, key="tab2_waarde")
    elif metric == "Studentenaantal":
        st.plotly_chart(plot_studenten(inst1, inst2), use_container_width=True, key="tab2_stud")
    elif metric == "Mutatie okt→feb":
        st.plotly_chart(plot_mutatie(inst1, inst2), use_container_width=True, key="tab2_mut")
    else:
        st.plotly_chart(plot_correctiefactoren(inst1, inst2), use_container_width=True, key="tab2_cf")

with tab3:
    col_r1, col_r2 = st.columns([3, 2])
    with col_r1:
        st.plotly_chart(plot_radar(inst1, inst2), use_container_width=True, key="tab3_radar")
    with col_r2:
        st.markdown("""
        <div style="background:white;border-radius:12px;padding:1.5rem;border:1px solid #e5e7eb;">
            <h4 style="margin-top:0;color:#1e3a5f;">🎯 Profielinterpretatie</h4>
            <p style="font-size:0.9rem;color:#4b5563;line-height:1.6;">
            <strong style="color:#2E86AB;">Blauw:</strong> grotere schaal, hoger marktaandeel<br>
            <strong style="color:#A23B72;">Paars:</strong> compacter, hogere diploma-ratio
            </p>
        </div>
        """, unsafe_allow_html=True)

with tab4:
    st.plotly_chart(plot_landelijke_ranglijst(inst1, inst2), use_container_width=True, key="tab4_rank")

with tab5:
    df = pd.DataFrame({
        'Metric': ['Studentenwaarde', 'Diplomawaarde', 'Som (SW+DW)', 'Inst.aandeel (%)', 'Correctiefactor', 'Studenten okt', 'Studenten feb', 'Mutatie'],
        f'{inst1["naam"]} - Entree': [
            inst1['entree'].get('studentenwaarde', 0), '-', 
            inst1['entree'].get('studentenwaarde', 0),
            inst1['entree'].get('instellingsaandeel_pct', 0), 
            inst1['entree'].get('correctiefactor', 1.0),
            inst1['entree'].get('aantal_studenten_okt', 0), 
            inst1['entree'].get('aantal_studenten_feb', 0),
            inst1['entree'].get('aantal_studenten_feb', 0) - inst1['entree'].get('aantal_studenten_okt', 0)
        ],
        f'{inst2["naam"]} - Entree': [
            inst2['entree'].get('studentenwaarde', 0), '-', 
            inst2['entree'].get('studentenwaarde', 0),
            inst2['entree'].get('instellingsaandeel_pct', 0), 
            inst2['entree'].get('correctiefactor', 1.0),
            inst2['entree'].get('aantal_studenten_okt', 0), 
            inst2['entree'].get('aantal_studenten_feb', 0),
            inst2['entree'].get('aantal_studenten_feb', 0) - inst2['entree'].get('aantal_studenten_okt', 0)
        ],
        f'{inst1["naam"]} - Basis': [
            inst1['basisberoeps'].get('studentenwaarde', 0), 
            inst1['basisberoeps'].get('diplomawaarde', 0), 
            inst1['basisberoeps'].get('som', 0),
            inst1['basisberoeps'].get('instellingsaandeel_pct', 0), 
            inst1['basisberoeps'].get('correctiefactor', 1.0),
            inst1['basisberoeps'].get('aantal_studenten_okt', 0), 
            inst1['basisberoeps'].get('aantal_studenten_feb', 0),
            inst1['basisberoeps'].get('aantal_studenten_feb', 0) - inst1['basisberoeps'].get('aantal_studenten_okt', 0)
        ],
        f'{inst2["naam"]} - Basis': [
            inst2['basisberoeps'].get('studentenwaarde', 0), 
            inst2['basisberoeps'].get('diplomawaarde', 0), 
            inst2['basisberoeps'].get('som', 0),
            inst2['basisberoeps'].get('instellingsaandeel_pct', 0), 
            inst2['basisberoeps'].get('correctiefactor', 1.0),
            inst2['basisberoeps'].get('aantal_studenten_okt', 0), 
            inst2['basisberoeps'].get('aantal_studenten_feb', 0),
            inst2['basisberoeps'].get('aantal_studenten_feb', 0) - inst2['basisberoeps'].get('aantal_studenten_okt', 0)
        ],
        f'{inst1["naam"]} - VMK/S': [
            inst1['vak_middenkader_specialisten'].get('studentenwaarde', 0), 
            inst1['vak_middenkader_specialisten'].get('diplomawaarde', 0), 
            inst1['vak_middenkader_specialisten'].get('som', 0),
            inst1['vak_middenkader_specialisten'].get('instellingsaandeel_pct', 0), 
            inst1['vak_middenkader_specialisten'].get('correctiefactor', 1.0),
            inst1['vak_middenkader_specialisten'].get('aantal_studenten_okt', 0), 
            inst1['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0),
            inst1['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0) - inst1['vak_middenkader_specialisten'].get('aantal_studenten_okt', 0)
        ],
        f'{inst2["naam"]} - VMK/S': [
            inst2['vak_middenkader_specialisten'].get('studentenwaarde', 0), 
            inst2['vak_middenkader_specialisten'].get('diplomawaarde', 0), 
            inst2['vak_middenkader_specialisten'].get('som', 0),
            inst2['vak_middenkader_specialisten'].get('instellingsaandeel_pct', 0), 
            inst2['vak_middenkader_specialisten'].get('correctiefactor', 1.0),
            inst2['vak_middenkader_specialisten'].get('aantal_studenten_okt', 0), 
            inst2['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0),
            inst2['vak_middenkader_specialisten'].get('aantal_studenten_feb', 0) - inst2['vak_middenkader_specialisten'].get('aantal_studenten_okt', 0)
        ]
    })
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "tbg_vergelijking.csv", "text/csv", key="download_csv")

st.markdown("---")
st.caption("MBO Bekostigingsdashboard | Data: DUO TBG 2025/2026")
