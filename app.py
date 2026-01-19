import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Gabrysia's Grocery", layout="wide", initial_sidebar_state="expanded")

# Stylizacja CSS
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
    st.error("❌ Błąd konfiguracji Secrets. Sprawdź parametry w Streamlit Cloud.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("➕ Zarządzanie")
    
    # Dodawanie Kategorii
    with st.expander("Nowa Kategoria"):
        with st.form("cat_form", clear_on_submit=True):
            k_kod = st.text_input("Kod")
            k_nazwa = st.text_input("Nazwa")
            if st.form_submit_button("Zapisz kategorię"):
                if k_kod and k_nazwa:
                    supabase.table("Kategoria").insert({"kod": k_kod, "nazwa": k_nazwa}).execute()
                    st.success("Dodano!")
                    st.rerun()

    # Dodawanie Produktu
    with st.expander("Nowy Produkt", expanded=True):
        try:
            k_res = supabase.table("Kategoria").select("id, nazwa").execute()
            k_dict = {item['nazwa']: item['id'] for item in k_res.data}
            
            if k_dict:
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
                                "cena": p_cena, 
                                "kategoria_id": k_dict[p_kat]
                            }).execute()
                            st.toast("Produkt dodany!")
                            st.rerun()
            else:
                st.warning("Najpierw stwórz kategorię.")
        except:
            st.error("Błąd ładowania kategorii.")

    # USUWANIE PRODUKTU
    st.divider()
    st.title("🗑️ Usuwanie")
    with st.expander("Usuń z bazy"):
        try:
            p_res = supabase.table("produkt").select("id, nazwa").execute()
            if p_res.data:
                produkty = {item['nazwa']: item['id'] for item in p_res.data}
                p_do_usuniecia = st.selectbox("Wybierz produkt", options=list(produkty.keys()))
                if st.button("Usuń bezpowrotnie", type="primary"):
                    supabase.table("produkt").delete().eq("id", produkty[p_do_usuniecia]).execute()
                    st.success("Usunięto!")
                    st.rerun()
            else:
                st.info("Brak produktów.")
        except:
            st.info("Brak danych.")

# --- DASHBOARD ---
try:
    res = supabase.table("produkt").select("nazwa, liczba, cena, Kategoria(nazwa)").execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df['kategoria_nazwa'] = df['Kategoria'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")

        # Metryki
        col1, col2, col3 = st.columns(3)
        col1.metric("🛒 Produkty", len(df))
        col2.metric("📦 Sztuki", int(df['liczba'].sum()))
        wartosc = (df['liczba'] * df['cena']).sum()
        col3.metric("💰 Wartość", f"{wartosc:,.2f} PLN")

        st.divider()

        # Wykresy
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(df, x="nazwa", y="liczba", color="kategoria_nazwa", title="Ilość", template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.bar(df, x="nazwa", y="cena", title="Cena PLN", template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📋 Pełna lista")
        st.dataframe(df[['nazwa', 'kategoria_nazwa', 'liczba', 'cena']], use_container_width=True)
    else:
        st.info("Baza jest pusta.")
except Exception as e:
    st.error(f"Błąd: {e}")
