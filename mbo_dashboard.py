import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="MBO Studentenaantallen Dashboard",
    page_icon="🎓",
    layout="wide"
)

# --- DATA LADEN MET CACHING ---
# De @st.cache_data decorator zorgt ervoor dat de data maar één keer wordt gedownload en verwerkt.
# Dit maakt het dashboard veel sneller na de eerste keer laden.
@st.cache_data
def load_data():
    """Laadt en transformeert de MBO studentendata van de DUO-website."""
    url = "https://duo.nl/open_onderwijsdata/images/studenten-per-type-mbo-niveau-woongemeente-provincie-deelnemer-leeftijd-2020-2024.csv"
    try:
        # De data van DUO gebruikt een puntkomma (;) als scheidingsteken.
        df = pd.read_csv(url, sep=';')
        
        # Hernoem kolommen voor beter leesbare code
        df.rename(columns={
            'OPLEIDINGSJAAR': 'jaar',
            'PROVINCIE WOONGEMEENTE': 'provincie',
            'WOONGEMEENTE': 'gemeente',
            'MBO OPLEIDINGSNIVEAU': 'niveau',
            'GESLACHT DEELNEMER': 'geslacht',
            'AANTAL DEELNEMERS': 'aantal_studenten'
        }, inplace=True)
        
        # Zorg ervoor dat 'aantal_studenten' een numeriek type is.
        # DUO kan soms '.' gebruiken voor kleine aantallen. We vervangen dit met 0.
        df['aantal_studenten'] = pd.to_numeric(df['aantal_studenten'], errors='coerce').fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Fout bij het laden van de data: {e}")
        return None

# Laad de data
df = load_data()

# Als het laden van de data mislukt, stop de uitvoering van de app
if df is None:
    st.stop()

# --- SIDEBAR MET FILTERS ---
st.sidebar.header("📊 Filters")

# Filter voor jaartal (range slider)
jaar_selectie = st.sidebar.slider(
    'Selecteer een periode:',
    min_value=int(df['jaar'].min()),
    max_value=int(df['jaar'].max()),
    value=(int(df['jaar'].min()), int(df['jaar'].max()))
)

# Filter voor provincie (multiselect)
provincie_selectie = st.sidebar.multiselect(
    'Selecteer provincie(s):',
    options=sorted(df['provincie'].unique()),
    default=sorted(df['provincie'].unique())
)

# Filter voor opleidingsniveau (multiselect)
niveau_selectie = st.sidebar.multiselect(
    'Selecteer MBO-niveau(s):',
    options=sorted(df['niveau'].unique()),
    default=sorted(df['niveau'].unique())
)

# Filter voor geslacht (multiselect)
geslacht_selectie = st.sidebar.multiselect(
    'Selecteer geslacht:',
    options=sorted(df['geslacht'].unique()),
    default=sorted(df['geslacht'].unique())
)

# --- FILTER DE DATA OP BASIS VAN DE SELECTIES ---
df_filtered = df[
    (df['jaar'].between(jaar_selectie[0], jaar_selectie[1])) &
    (df['provincie'].isin(provincie_selectie)) &
    (df['niveau'].isin(niveau_selectie)) &
    (df['geslacht'].isin(geslacht_selectie))
]

# --- HOOFDPAGINA ---
st.title("🎓 Dashboard MBO Studentenaantallen 2020-2024")
st.markdown("""
Dit interactieve dashboard toont de ontwikkeling van het aantal studenten in het Middelbaar Beroepsonderwijs (MBO) in Nederland.
Gebruik de filters in de zijbalk om de data te verkennen. De visualisaties worden automatisch bijgewerkt.
*Bron: DUO Open Onderwijsdata*
""")
st.markdown("---")


# --- KPI'S (KEY PERFORMANCE INDICATORS) ---
if not df_filtered.empty:
    # Bereken KPI's
    totaal_studenten_eindjaar = df_filtered[df_filtered['jaar'] == jaar_selectie[1]]['aantal_studenten'].sum()
    
    start_jaar_studenten = df_filtered[df_filtered['jaar'] == jaar_selectie[0]]['aantal_studenten'].sum()
    eind_jaar_studenten = df_filtered[df_filtered['jaar'] == jaar_selectie[1]]['aantal_studenten'].sum()
    
    # Voorkom delen door nul als startjaar geen data heeft of hetzelfde is als eindjaar
    if start_jaar_studenten > 0 and jaar_selectie[0] != jaar_selectie[1]:
        procentuele_groei = ((eind_jaar_studenten - start_jaar_studenten) / start_jaar_studenten) * 100
    else:
        procentuele_groei = 0

    aantal_gemeenten = df_filtered['gemeente'].nunique()

    # Toon KPI's in kolommen
    col1, col2, col3 = st.columns(3)
    col1.metric(
        label=f"Totaal Studenten in {jaar_selectie[1]}", 
        value=f"{totaal_studenten_eindjaar:,.0f}".replace(",", ".")
    )
    col2.metric(
        label=f"Groei ({jaar_selectie[0]}-{jaar_selectie[1]})", 
        value=f"{procentuele_groei:.1f}%"
    )
    col3.metric(
        label="Aantal Unieke Gemeenten", 
        value=aantal_gemeenten
    )
else:
    st.warning("Geen data beschikbaar voor de geselecteerde filters.")
    st.stop()

st.markdown("---")

# --- VISUALISATIES ---

# 1. Ontwikkeling van studentenaantallen per jaar (Lijngrafiek)
st.subheader("Ontwikkeling Aantal Studenten per Jaar")
studenten_per_jaar = df_filtered.groupby('jaar')['aantal_studenten'].sum().reset_index()

fig_lijn = px.line(
    studenten_per_jaar,
    x='jaar',
    y='aantal_studenten',
    title='Totaal Aantal Studenten per Jaar',
    labels={'jaar': 'Jaar', 'aantal_studenten': 'Aantal Studenten'},
    markers=True
)
fig_lijn.update_layout(xaxis=dict(tickmode='linear')) # Zorgt ervoor dat alle jaartallen worden getoond
st.plotly_chart(fig_lijn, use_container_width=True)


# Maak twee kolommen voor de volgende grafieken
col_vis1, col_vis2 = st.columns(2)

with col_vis1:
    # 2. Verdeling per MBO-niveau (Staafdiagram)
    st.subheader("Verdeling per MBO-Niveau")
    studenten_per_niveau = df_filtered.groupby('niveau')['aantal_studenten'].sum().sort_values(ascending=False).reset_index()
    
    fig_niveau = px.bar(
        studenten_per_niveau,
        x='aantal_studenten',
        y='niveau',
        orientation='h',
        title='Aantal Studenten per Opleidingsniveau',
        labels={'niveau': 'Opleidingsniveau', 'aantal_studenten': 'Aantal Studenten'},
        text='aantal_studenten'
    )
    fig_niveau.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_niveau.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_niveau, use_container_width=True)

with col_vis2:
    # 3. Verdeling naar geslacht (Cirkeldiagram)
    st.subheader("Verdeling naar Geslacht")
    studenten_per_geslacht = df_filtered.groupby('geslacht')['aantal_studenten'].sum().reset_index()

    fig_geslacht = px.pie(
        studenten_per_geslacht,
        names='geslacht',
        values='aantal_studenten',
        title='Verdeling Studenten naar Geslacht',
        hole=0.3
    )
    st.plotly_chart(fig_geslacht, use_container_width=True)


# 4. Verdeling per provincie (Staafdiagram)
st.subheader("Aantal Studenten per Provincie")
studenten_per_provincie = df_filtered.groupby('provincie')['aantal_studenten'].sum().sort_values(ascending=False).reset_index()

fig_provincie = px.bar(
    studenten_per_provincie,
    x='provincie',
    y='aantal_studenten',
    title='Totaal Aantal Studenten per Provincie',
    labels={'provincie': 'Provincie', 'aantal_studenten': 'Aantal Studenten'},
    color='provincie',
    color_discrete_sequence=px.colors.qualitative.Prism
)
st.plotly_chart(fig_provincie, use_container_width=True)


# --- DATA TABEL ---
st.subheader("Gefilterde Data")
st.markdown("Hieronder staat een overzicht van de data op basis van de geselecteerde filters.")

# Toon een samengevatte, gegroepeerde tabel voor de duidelijkheid
df_display = df_filtered.groupby(['jaar', 'provincie', 'gemeente', 'niveau', 'geslacht'])['aantal_studenten'].sum().reset_index()
st.dataframe(df_display)
