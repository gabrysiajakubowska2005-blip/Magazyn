import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Gabrysia's Grocery", layout="wide", initial_sidebar_state="expanded")

# Custom CSS dla nowoczesnego wyglądu
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

# --- NAGŁÓWEK APLIKACJI ---
st.markdown('<div class="main-title"><h1>🍎 Gabrysia\'s grocery Magazine</h1></div>', unsafe_allow_html=True)

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
    
    with st.expander("Nowa Kategoria"):
        with st.form("cat_form", clear_on_submit=True):
            k_kod = st.text_input("Kod")
            k_nazwa = st.text_input("Nazwa")
            if st.form_submit_button("Zapisz"):
                if k_kod and k_nazwa:
                    supabase.table("Kategoria").insert({"kod": k_kod, "nazwa": k_nazwa}).execute()
                    st.success("Dodano!")
                    st.rerun()

    with st.expander("Nowy Produkt", expanded=True):
        try:
            k_res = supabase.table("Kategoria").select("id, nazwa").execute()
            k_dict = {item['nazwa']: item['id'] for item in k_res.data}
            
            with st.form("prod_form", clear_on_submit=True):
                p_nazwa = st.text_input("Nazwa produktu")
                p_liczba = st.number_input("Ilość", min_value=0)
                p_cena = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                p_kat = st.selectbox("Kategoria", options=list(k_dict.keys()))
                
                if st.form_submit_button("Zapisz Produkt"):
                    if p_nazwa:
                        supabase.table("produkt").insert({
                            "nazwa": p_nazwa, "liczba": p_liczba, 
                            "cena": p_cena, "kategoria_id": k_dict[p_kat]
                        }).execute()
                        st.toast("Produkt dodany!", icon="✅")
                        st.rerun()
        except:
            st.warning("Najpierw dodaj kategorię!")

# --- PANEL GŁÓWNY (DASHBOARD) ---
try:
    # Zwróć uwagę na nazwę tabeli: "produkt" czy "produkty"?
    res = supabase.table("produkt").select("nazwa, liczba, cena, Kategoria(nazwa)").execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df['kategoria_nazwa'] = df['Kategoria'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")

        # METRYKI
        m1, m2, m3 = st.columns(3)
        m1.metric("🛒 Rodzaje produktów", len(df))
        m2.metric("📦 Łączna ilość sztuk", int(df['liczba'].sum()))
        total_val = (df['liczba'] * df['cena']).sum()
        m3.metric("💰 Wartość zapasów", f"{total_val:,.2f} PLN")

        st.divider()

        # WYKRESY
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Ilość towaru")
            fig_qty = px.bar(df, x="nazwa", y="liczba", color="kategoria_nazwa",
                             color_discrete_sequence=px.colors.qualitative.Prism,
                             template="plotly_white")
            st.plotly_chart(fig_qty, use_container_width=True)

        with c2:
            st.subheader("Ceny produktów (PLN)")
            fig_price = px.bar(df.sort_values('cena'), x="nazwa", y="cena",
                               color_discrete_sequence=['#4caf50'],
                               template="plotly_white")
            st.plotly_chart(fig_price, use_container_width=True)

        st.subheader("📝 Lista asortymentu")
        st.dataframe(df[['nazwa', 'kategoria_nazwa', 'liczba', 'cena']], use_container_width=True)

    else:
        st.info("Baza danych jest pusta.")

except Exception as e:
    st.error(f"Błąd bazy danych: {e}")
