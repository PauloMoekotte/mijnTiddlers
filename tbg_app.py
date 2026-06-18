"""
TBG PDF Analyzer — Streamlit app
Upload een DUO Terugmelding Bekostigingsgrondslagen PDF
en bekijk de data in tabbladen met tabellen en grafieken.
"""

import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import urllib.request
import re
import os

st.set_page_config(page_title='TBG Analyse', page_icon='📊', layout='wide')

# ── DUO REFERENTIE (cached) ──

@st.cache_data(ttl=3600, show_spinner='DUO-referentie laden...')
def download_duo():
    url = 'https://www.duo.nl/open_onderwijsdata/images/combinatie-erkende-opleidingscode-en-beroep-2025-2026.csv'
    resp = urllib.request.urlopen(url)
    df = pd.read_csv(BytesIO(resp.read()), sep=';', low_memory=False)
    df['code'] = df['Erkende opleidingscode'].astype(str)
    lookup = {}
    for _, r in df.iterrows():
        c = r['code']
        if c not in lookup:
            lookup[c] = {
                'hoofdgroep': r.get('Hoofdgroep naam', '') or '',
                'subgroep': r.get('Subgroep naam', '') or '',
                'dossier': r.get('Dossier naam', '') or '',
                'sectorkamer': r.get('Sectorkamer naam', '') or '',
            }
    return lookup


# ── PDF PARSER ──

def _parse_num(s):
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except (ValueError, AttributeError):
        return 0.0


def parse_pdf_bytes(pdf_bytes):
    rows = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            for line in text.split('\n'):
                line = line.strip()
                if not re.match(r'^\d{5}\s', line):
                    continue
                tokens = line.split()
                if len(tokens) < 6:
                    continue
                code = int(tokens[0])
                idx = None
                leerweg = None
                for t in ('BOL', 'BBL'):
                    if t in tokens:
                        pos = tokens.index(t)
                        if pos >= 2 and pos < len(tokens) - 1:
                            try:
                                int(tokens[pos - 1])
                                _parse_num(tokens[pos + 1])
                                idx = pos
                                leerweg = t
                                break
                            except (ValueError, IndexError):
                                continue
                if idx is None:
                    continue
                niveau = int(tokens[idx - 1])
                if niveau not in (1, 2, 3, 4):
                    continue
                naam = ' '.join(tokens[1:idx - 1])
                nums = tokens[idx + 1:]
                if len(nums) < 3:
                    continue
                waarde = _parse_num(nums[-2])
                cnt = int(_parse_num(nums[0]))
                if waarde <= 0 and cnt <= 0:
                    continue
                rows.append({'crebo': code, 'naam': naam, 'niveau': niveau,
                             'leerweg': leerweg, 'sw': waarde})
    seen = set()
    uniq = []
    for r in rows:
        key = (r['crebo'], r['niveau'], r['leerweg'], r['sw'])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


# ── DATA VERWERKING ──

def verwerk_data(rows, lookup):
    for r in rows:
        c = str(r['crebo'])
        lu = lookup.get(c, {})
        r['hoofdgroep'] = lu.get('hoofdgroep', '') or ('Entree' if r['niveau'] == 1 else 'Onbekend')
        r['subgroep'] = lu.get('subgroep', '') or ('Entree' if r['niveau'] == 1 else 'Onbekend')
        r['sectorkamer'] = lu.get('sectorkamer', '') or ('Entree' if r['niveau'] == 1 else 'Onbekend')
    return rows


# ── UI ──

def main():
    st.title('📊 TBG PDF Analyzer')
    st.markdown(
        'Upload een **DUO Terugmelding Bekostigingsgrondslagen PDF** '
        'om de studentenwaarde-verdeling te bekijken per niveau, SBB-sector, '
        'hoofdgroep en subgroep.'
    )

    uploaded = st.file_uploader('Kies een TBG PDF', type='pdf')

    if not uploaded:
        st.info('Upload een PDF om te beginnen.', icon='📄')
        st.stop()

    with st.spinner('PDF verwerken...'):
        raw = parse_pdf_bytes(uploaded.read())

    if not raw:
        st.error('Geen opleidingsdata gevonden in deze PDF. Is het een geldige TBG?')
        st.stop()

    lookup = download_duo()
    data = verwerk_data(raw, lookup)
    df = pd.DataFrame(data)

    totaal_sw = df['sw'].sum()

    # ── KPI RIJ ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Opleidingsregels', len(df))
    with col2:
        st.metric('Totale studentenwaarde', f'{totaal_sw:,.2f}')
    with col3:
        st.metric('Unieke CREBO-codes', df['crebo'].nunique())
    with col4:
        niveaus = df['niveau'].value_counts()
        st.metric('Niveaus', ', '.join(str(n) for n in sorted(niveaus.index)))

    # ── TABBLADEN ──
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        '📋 Samenvatting', '🔵 Entree', '🟢 Basisberoeps', '🟠 Vak/MK/Spec',
        '🟣 SBB Sector', '🔴 Hoofdgroepen', '⚫ Subgroepen',
    ])

    def maak_staaf(df, x_kolom, y_kolom, titel, kleur=None):
        fig = px.bar(df, x=x_kolom, y=y_kolom, title=titel,
                     color=kleur, text_auto='.2s')
        fig.update_layout(xaxis_title='', yaxis_title='Studentenwaarde', height=500)
        st.plotly_chart(fig, use_container_width=True)

    # ══════════════════════════════════
    # TAB 1: SAMENVATTING
    # ══════════════════════════════════
    with tab1:
        st.subheader('Studentenwaarde per categorie')

        niv_labels = {1: 'Entree', 2: 'Basisberoeps', 3: 'Vak/middenkader/spec', 4: 'Vak/middenkader/spec'}
        df_niv = df.copy()
        df_niv['categorie'] = df_niv['niveau'].map(niv_labels)
        niv_tot = df_niv.groupby('categorie')['sw'].sum().reset_index()
        niv_tot['%'] = niv_tot['sw'] / totaal_sw * 100
        niv_order = ['Entree', 'Basisberoeps', 'Vak/middenkader/spec']
        niv_tot['categorie'] = pd.Categorical(niv_tot['categorie'], categories=niv_order, ordered=True)
        niv_tot = niv_tot.sort_values('categorie')

        col_a, col_b = st.columns([1, 1.5])
        with col_a:
            st.dataframe(niv_tot, use_container_width=True, hide_index=True,
                         column_config={
                             'categorie': st.column_config.TextColumn('Categorie'),
                             'sw': st.column_config.NumberColumn('Studentenwaarde', format='%.2f'),
                             '%': st.column_config.NumberColumn('% van totaal', format='%.2f%%'),
                         })
        with col_b:
            fig = px.pie(niv_tot, values='sw', names='categorie',
                          title='Verdeling per niveau-categorie')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader('Top 20 opleidingen naar studentenwaarde')
        top20 = df.nlargest(20, 'sw')[['naam', 'crebo', 'niveau', 'leerweg', 'sw', 'hoofdgroep']].copy()
        top20.insert(0, '#', range(1, len(top20) + 1))
        st.dataframe(top20, use_container_width=True, hide_index=True,
                     column_config={
                         'sw': st.column_config.NumberColumn('Studentenwaarde', format='%.2f'),
                     })

        fig = px.bar(top20, x='sw', y='naam', orientation='h',
                      title='Top 20 — Studentenwaarde per opleiding',
                      color='niveau', text_auto='.2s')
        fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'},
                          xaxis_title='Studentenwaarde', yaxis_title='')
        st.plotly_chart(fig, use_container_width=True)

    # ══════════════════════════════════
    # TAB 2-4: DETAILS PER NIVEAU
    # ══════════════════════════════════
    def detail_tab(tab, niveau_filter, titel):
        with tab:
            subset = df[df['niveau'] == niveau_filter] if niveau_filter < 3 else df[df['niveau'] >= 3]
            sub_sw = subset['sw'].sum()
            st.markdown(f'**{len(subset)}** regels · totale studentenwaarde: **{sub_sw:,.2f}**')
            toon = subset[['naam', 'crebo', 'niveau', 'leerweg', 'sw', 'hoofdgroep', 'subgroep']].copy()
            toon = toon.sort_values('sw', ascending=False)
            toon.insert(0, '#', range(1, len(toon) + 1))
            st.dataframe(toon, use_container_width=True, hide_index=True,
                         column_config={
                             'sw': st.column_config.NumberColumn('Studentenwaarde', format='%.2f'),
                         })
            maak_staaf(toon.head(20), 'sw', 'naam', f'Top 20 — {titel}')

    detail_tab(tab2, 1, 'Entree')
    detail_tab(tab3, 2, 'Basisberoeps')
    detail_tab(tab4, 3, 'Vak-/middenkader-/specialisten')

    # ══════════════════════════════════
    # TAB 5: SBB SECTORINDELING
    # ══════════════════════════════════
    with tab5:
        st.subheader('Verdeling naar SBB-sectorkamers')
        sk_tot = df.groupby('sectorkamer').agg(sw=('sw', 'sum'), count=('crebo', 'nunique')).reset_index()
        sk_tot.columns = ['SBB-sectorkamer', 'Studentenwaarde', 'Aantal opleidingen']
        sk_tot['% van totaal'] = sk_tot['Studentenwaarde'] / totaal_sw * 100
        sk_tot = sk_tot.sort_values('Studentenwaarde', ascending=False)

        col_a, col_b = st.columns([1, 1.5])
        with col_a:
            st.dataframe(sk_tot, use_container_width=True, hide_index=True,
                         column_config={
                             'Studentenwaarde': st.column_config.NumberColumn(format='%.2f'),
                             '% van totaal': st.column_config.NumberColumn(format='%.2f%%'),
                         })
        with col_b:
            fig = px.pie(sk_tot, values='Studentenwaarde', names='SBB-sectorkamer',
                          title='SBB-sectorkamers')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader('Studentenwaarde per SBB-sectorkamer')
        fig = px.bar(sk_tot, x='Studentenwaarde', y='SBB-sectorkamer', orientation='h',
                      text_auto='.2s', color='Studentenwaarde',
                      color_continuous_scale='Blues')
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'},
                          xaxis_title='Studentenwaarde', yaxis_title='')
        st.plotly_chart(fig, use_container_width=True)

    # ══════════════════════════════════
    # TAB 6: HOOFDGROEPEN
    # ══════════════════════════════════
    with tab6:
        st.subheader('Verdeling naar hoofdgroepen (opleidingsdomeinen)')
        hg_tot = df.groupby('hoofdgroep').agg(sw=('sw', 'sum'), count=('crebo', 'nunique')).reset_index()
        hg_tot.columns = ['Hoofdgroep (domein)', 'Studentenwaarde', 'Aantal opleidingen']
        hg_tot['% van totaal'] = hg_tot['Studentenwaarde'] / totaal_sw * 100
        hg_tot = hg_tot.sort_values('Studentenwaarde', ascending=False)

        col_a, col_b = st.columns([1, 1.5])
        with col_a:
            st.dataframe(hg_tot, use_container_width=True, hide_index=True,
                         column_config={
                             'Studentenwaarde': st.column_config.NumberColumn(format='%.2f'),
                             '% van totaal': st.column_config.NumberColumn(format='%.2f%%'),
                         })
        with col_b:
            fig = px.pie(hg_tot, values='Studentenwaarde', names='Hoofdgroep (domein)',
                          title='Opleidingsdomeinen')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader('Studentenwaarde per hoofdgroep')
        fig = px.bar(hg_tot, x='Studentenwaarde', y='Hoofdgroep (domein)', orientation='h',
                      text_auto='.2s', color='Studentenwaarde',
                      color_continuous_scale='Reds')
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'},
                          xaxis_title='Studentenwaarde', yaxis_title='')
        st.plotly_chart(fig, use_container_width=True)

    # ══════════════════════════════════
    # TAB 7: SUBGROEPEN
    # ══════════════════════════════════
    with tab7:
        st.subheader('Verdeling naar subgroepen (kwalificatiedossier-niveau)')
        sg = df.groupby(['hoofdgroep', 'subgroep'])['sw'].sum().reset_index()
        sg = sg.sort_values(['hoofdgroep', 'sw'], ascending=[True, False])
        sg['% van totaal'] = sg['sw'] / totaal_sw * 100

        hg_t = sg.groupby('hoofdgroep')['sw'].transform('sum')
        sg['% binnen hoofdgroep'] = sg['sw'] / hg_t * 100

        st.dataframe(sg, use_container_width=True, hide_index=True,
                     column_config={
                         'sw': st.column_config.NumberColumn('Studentenwaarde', format='%.2f'),
                         '% van totaal': st.column_config.NumberColumn(format='%.2f%%'),
                         '% binnen hoofdgroep': st.column_config.NumberColumn(format='%.2f%%'),
                     })

        st.divider()
        st.subheader('Top 15 subgroepen')
        top15 = sg.nlargest(15, 'sw')
        fig = px.pie(top15, values='sw', names='subgroep', title='Top 15 subgroepen')
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader('Subgroepen — staafdiagram')
        fig = px.bar(top15, x='sw', y='subgroep', orientation='h',
                      color='hoofdgroep', text_auto='.2s',
                      title='Top 15 subgroepen naar studentenwaarde')
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'},
                          xaxis_title='Studentenwaarde', yaxis_title='')
        st.plotly_chart(fig, use_container_width=True)

    # ── FOOTER ──
    st.divider()
    st.caption(f'Verwerkt: {uploaded.name} | {len(df)} regels | Studentenwaarde: {totaal_sw:,.2f}')


if __name__ == '__main__':
    main()
