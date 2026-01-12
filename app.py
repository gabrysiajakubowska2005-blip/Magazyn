import streamlit as st
from supabase import create_client, Client

# 1. Konfiguracja połączenia z Supabase
# Upewnij się, że te dane są w Streamlit Cloud -> Settings -> Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji Secrets. Sprawdź czy dodałeś SUPABASE_URL i SUPABASE_KEY.")
    st.stop()

st.title("📦 System Magazynowy")

# --- SEKCJA 1: DODAWANIE KATEGORII ---
st.header("1. Dodaj nową kategorię")
with st.form("category_form", clear_on_submit=True):
    kat_kod = st.text_input("Kod kategorii (np. AGD-01)")
    kat_nazwa = st.text_input("Nazwa kategorii")
    kat_opis = st.text_area("Opis")
    
    submit_kat = st.form_submit_button("Zapisz kategorię")
    
    if submit_kat:
        if kat_kod and kat_nazwa:
            data = {"kod": kat_kod, "nazwa": kat_nazwa, "opis": kat_opis}
            try:
                supabase.table("Kategoria").insert(data).execute()
                st.success(f"Dodano kategorię: {kat_nazwa}")
            except Exception as e:
                st.error(f"Błąd bazy danych: {e}")
        else:
            st.warning("Kod i nazwa są wymagane!")

# Linia oddzielająca (zastępuje <hr>)
st.divider()

# --- SEKCJA 2: DODAWANIE PRODUKTÓW ---
st.header("2. Dodaj nowy produkt")

# Pobieranie listy kategorii do rozwijanego menu
try:
    kategorie_res = supabase.table("Kategoria").select("id, nazwa").execute()
    # Tworzymy słownik {Nazwa: ID}, aby użytkownik widział nazwę, a baza dostała ID
    kategorie_dict = {item['nazwa']: item['id'] for item in kategorie_res.data}
except Exception as e:
    kategorie_dict = {}
    st.error("Nie można pobrać kategorii. Dodaj najpierw przynajmniej jedną kategorię.")

with st.form("product_form", clear_on_submit=True):
    prod_nazwa = st
