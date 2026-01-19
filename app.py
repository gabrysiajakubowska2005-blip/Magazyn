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
    st.error("❌ Błąd połączenia. Sprawdź Secrets w Streamlit Cloud.")
    st.stop()

# --- SIDEBAR: DODAWANIE ---
with st.sidebar:
    st.title("➕ Dodaj Nowe")
    
    with st.expander("Nowa Kategoria"):
        with st.form("cat_form", clear_on_submit=True):
            k_kod = st.text_input("Kod (np. NAB)")
            k_nazwa = st.text_input("Nazwa (np. Nabiał)")
            if st.form_submit_button("Dodaj"):
                if k_kod and k_nazwa:
                    supabase.table("Kategoria").insert({"kod": k_kod, "nazwa": k_nazwa}).execute()
                    st.success("Dodano!")
                    st.rerun()

    with st.expander("Nowy Produkt"):
        k_res = supabase.table("Kategoria").select("id, nazwa").execute()
        k_dict = {item['nazwa']: item['id'] for item in k_res.data}
        if k_dict:
            with st.form("prod_form", clear_on_submit=True):
                p_nazwa = st.text_input("Nazwa")
                p_liczba = st.number_input("Ilość", min_value=0, step=1)
                p_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
                p_kat = st.selectbox("Kategoria", options=list(k_dict.keys()))
                if st.form_submit_button("Zapisz"):
                    supabase.table("produkt").insert({
                        "nazwa": p_nazwa, "liczba": p_liczba, "cena": p_cena, "kategoria_id": k_dict[p_kat]
                    }).execute()
                    st.rerun()

    # --- EDYCJA I USUWANIE ---
    st.divider()
    st.title("⚙️ Zarządzaj")

    # 1. ZMIANA ILOŚCI
    with st.expander("Zmień Ilość Sztuk"):
        p_res = supabase.table("produkt").select("id, nazwa, liczba").execute()
        if p_res.data:
            p_options = {item['nazwa']: item for item in p_res.data}
            sel_p_name = st.selectbox("Wybierz produkt", options=list(p_options.keys()), key="edit_qty_sel")
            current_qty = p_options[sel_p_name]['liczba']
            new_qty = st.number_input("Nowa ilość", value=int(current_qty), min_value=0)
            if st.button("Aktualizuj ilość"):
                supabase.table("produkt").update({"liczba": new_qty}).eq("id", p_options[sel_p_name]['id']).execute()
                st.success("Zmieniono!")
                st.rerun()

    # 2. USUWANIE PRODUKTU
    with st.expander("Usuń Produkt"):
        if p_res.data:
            p_to_del = st.selectbox("Produkt do usunięcia", options=list(p_options.keys()), key="del_prod_sel")
            if st.button("USUŃ PRODUKT", type="primary"):
                supabase.table("produkt").delete().eq("id", p_options[p_to_del]['id']).execute()
                st.rerun()

    # 3. USUWANIE KATEGORII
    with st.expander("Usuń Kategorię"):
        if k_dict:
            kat_to_del = st.selectbox("Kategoria do usunięcia", options=list(k_dict.keys()))
            if st.button("USUŃ KATEGORIĘ", type="primary"):
                # Sprawdzenie czy kategoria jest pusta
                check_p = supabase.table("produkt").select("id").eq("kategoria_id", k_dict[kat_to_del]).execute()
                if len(check_p.data) > 0:
                    st.error("Nie można usunąć! Ta kategoria zawiera produkty.")
                else:
                    supabase.table("Kategoria").delete().eq("id", k_dict[kat_to_del]).execute()
                    st.success("Usunięto!")
                    st.rerun()

# --- PANEL GŁÓWNY ---
try:
    res = supabase.table("produkt").select("nazwa, liczba, cena, Kategoria(nazwa)").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df['kategoria_nazwa'] = df['Kategoria'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")

        m1, m2, m3 = st.columns(3)
        m1.metric("🛒 Produkty", len(df))
        m2.metric("📦 Sztuki", int(df['liczba'].sum()))
        m3.metric("💰 Wartość", f"{(df['liczba'] * df['cena']).sum():,.2f} PLN")

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.bar(df, x="nazwa", y="liczba", color="kategoria_nazwa", title="Stan magazynowy"), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(df, x="nazwa", y="cena", title="Cena PLN"), use_container_width=True)

        st.subheader("📋 Tabela asortymentu")
        st.dataframe(df[['nazwa', 'kategoria_nazwa', 'liczba', 'cena']], use_container_width=True)
    else:
        st.info("Baza jest pusta.")
except Exception as e:
    st.error(f"Błąd: {e}")
