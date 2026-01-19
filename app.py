import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Gabrysia's Grocery", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
    <style>
    .main-title {
        font-family: 'Helvetica Neue', sans-serif;
        color: #2e7d32;
        text-align: center;
        padding: 20px;
        background: #e8f5e9;
        border-radius: 15px;
        margin-bottom: 30px;
        border-left: 10px solid #4caf50;
    }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title"><h1>🍎 Gabrysia\'s Grocery Magazine</h1></div>', unsafe_allow_html=True)

# 1. Połączenie z Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("❌ Błąd konfiguracji Secrets. Sprawdź SUPABASE_URL i SUPABASE_KEY.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("➕ Zarządzanie")
    
    # SEKCJA: NOWA KATEGORIA
    with st.expander("Nowa Kategoria"):
        with st.form("cat_form", clear_on_submit=True):
            k_kod = st.text_input("Kod (np. OWOC)")
            k_nazwa = st.text_input("Nazwa (np. Owoce)")
            if st.form_submit_button("Dodaj Kategorię"):
                if k_kod and k_nazwa:
                    supabase.table("Kategoria").insert({"kod": k_kod, "nazwa": k_nazwa}).execute()
                    st.success("Kategoria dodana!")
                    st.rerun()

    # SEKCJA: NOWY PRODUKT
    with st.expander("Nowy Produkt", expanded=True):
        try:
            k_res = supabase.table("Kategoria").select("id, nazwa").execute()
            k_dict = {item['nazwa']: item['id'] for item in k_res.data}
            
            if not k_dict:
                st.warning("Najpierw dodaj kategorię!")
            else:
                with st.form("prod_form", clear_on_submit=True):
                    p_nazwa = st.text_input("Nazwa produktu")
                    p_liczba = st.number_input("Ilość", min_value=0, step=1)
                    p_cena = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                    p_kat = st.selectbox("Kategoria", options=list(k_dict.keys()))
                    
                    if st.form_submit_button("Zapisz Produkt"):
                        if p_nazwa:
                            supabase.table("produkt").insert({
                                "nazwa": p_nazwa, 
                                "liczba": p_liczba,
