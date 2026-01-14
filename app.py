import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Smart Inventory", layout="wide", initial_sidebar_state="expanded")

# Custom CSS dla nowoczesnego wyglądu
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 1. Konfiguracja połączenia z Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji Secrets. Sprawdź ustawienia.")
    st.stop()

# --- SIDEBAR: DODAWANIE DANYCH ---
with st.sidebar:
    st.title("➕ Zarządzanie")
    
    with st.expander("Nowa Kategoria", expanded=False):
        with st.form("category_form", clear_on_submit=True):
            kat_kod = st.text_input("Kod")
            kat_nazwa = st.text_input("Nazwa")
            submit_kat = st.form_submit_button("Dodaj")
            if submit_kat and kat_kod and kat_nazwa:
                supabase.table("Kategoria").insert({"kod": kat_kod, "nazwa": kat_nazwa}).execute()
                st.toast("Dodano kategorię!", icon="✅")

    with st.expander("Nowy Produkt", expanded=True):
        try:
            k_res = supabase.table("Kategoria").select("id, nazwa").execute()
            k_dict = {item['nazwa']: item['id'] for item in k_res.data}
            
            with st.form("product_form", clear_on_submit=True):
                p_nazwa = st.text_input("Nazwa produktu")
                p_liczba = st.number_input("Ilość", min_value=0)
                p_cena = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                p_kat = st.selectbox("Kategoria", options=list(k_dict.keys()))
                submit_prod = st.form_submit_button("Zapisz Produkt")
                
                if submit_prod and p_nazwa:
                    supabase.table("produkt").insert({
                        "nazwa": p_nazwa, "liczba": p_liczba, 
                        "cena": p_cena, "kategoria_id": k_dict[p_kat]
                    }).execute()
                    st.toast("Produkt dodany!", icon="📦")
        except:
            st.warning("Najpierw dodaj kategorię.")

# --- PANEL GŁÓWNY (DASHBOARD) ---
st.title("📊 Dashboard Magazynowy")

# Pobieranie danych
try:
    res = supabase.table("produkt").select("nazwa, liczba, cena, Kategoria(nazwa)").execute()
    df = pd.DataFrame(res.data)
    
    if not df.empty:
        # Przetwarzanie nazwy kategorii z relacji JSON
        df['kategoria_nazwa'] = df['Kategoria'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
        
        # --- METRYKI ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Liczba Produktów", len(df))
        m2.metric("Łączna ilość sztuk", df['liczba'].sum())
        m3.metric("Wartość Magazynu", f"{ (df['liczba'] * df['cena']).sum():,.2f} PLN")

        st.divider()

        # --- WYKRESY ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📦 Ilość sztuk na magazynie")
            fig_qty = px.bar(df, x="nazwa", y="liczba", color="kategoria_nazwa",
                             labels={'liczba': 'Sztuki', 'nazwa': 'Produkt'},
                             template="plotly_white", color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_qty, use_container_width=True)

        with col_right:
            st.subheader("💰 Porównanie cen produktów")
            fig_price = px.line(df.sort_values('cena'), x="nazwa", y="cena", 
                                markers=True, labels={'cena': 'Cena (PLN)'},
                                template="plotly_white")
            fig_price.update_traces(line_color='#2ecc71', line_width=3)
            st.plotly_chart(fig_price, use_container_width=True)

        # --- TABELA DANYCH ---
        st.subheader("📝 Szczegółowa lista")
        st.dataframe(df[['nazwa', 'kategoria_nazwa', 'liczba', 'cena']], use_container_width=True)

    else:
        st.info("Brak danych do wyświetlenia. Skorzystaj z panelu bocznego, aby dodać produkty.")

except Exception as e:
    st.error(f"Wystąpił błąd podczas ładowania danych: {e}")
