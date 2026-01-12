import streamlit as st
from supabase import create_client, Client

# 1. Konfiguracja połączenia z Supabase
# W Streamlit Cloud dodaj te dane w zakładce "Secrets"
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📦 Zarządzanie Bazą Produktów")

# --- SEKCJA 1: DODAWANIE KATEGORII ---
st.header("Dodaj nową kategorię")
with st.form("category_form", clear_on_submit=True):
    kat_kod = st.text_input("Kod kategorii (np. ELE-01)")
    kat_nazwa = st.text_input("Nazwa kategorii")
    kat_opis = st.text_area("Opis")
    
    submit_kat = st.form_submit_button("Zapisz kategorię")
    
    if submit_kat:
        data = {"kod": kat_kod, "nazwa": kat_nazwa, "opis": kat_opis}
        try:
            response = supabase.table("Kategoria").insert(data).execute()
            st.success("Dodano kategorię!")
        except Exception as e:
            st.error(f"Błąd: {e}")

<hr>

# --- SEKCJA 2: DODAWANIE PRODUKTÓW ---
st.header("Dodaj nowy produkt")

# Pobieranie listy kategorii do rozwijanego menu (select box)
try:
    kategorie_res = supabase.table("Kategoria").select("id, nazwa").execute()
    lista_kategorii = {item['nazwa']: item['id'] for item in kategorie_res.data}
except Exception as e:
    lista_kategorii = {}
    st.error("Nie udało się pobrać kategorii.")

with st.form("product_form", clear_on_submit=True):
    prod_nazwa = st.text_input("Nazwa produktu")
    prod_liczba = st.number_input("Liczba sztuk", min_value=0, step=1)
    prod_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
    
    # Wybór kategorii z listy
    wybrana_kat = st.selectbox("Wybierz kategorię", options=list(lista_kategorii.keys()))
    
    submit_prod = st.form_submit_button("Zapisz produkt")
    
    if submit_prod:
        data_prod = {
            "nazwa": prod_nazwa,
            "liczba": prod_liczba,
            "cena": prod_cena,
            "kategoria_id": lista_kategorii[wybrana_kat]
        }
        try:
            supabase.table("produkt").insert(data_prod).execute()
            st.success(f"Dodano produkt: {prod_nazwa}")
        except Exception as e:
            st.error(f"Błąd podczas dodawania produktu: {e}")

# --- SEKCJA 3: PODGLĄD DANYCH ---
if st.checkbox("Pokaż listę produktów"):
    res = supabase.table("produkt").select("nazwa, liczba, cena, Kategoria(nazwa)").execute()
    st.table(res.data)
